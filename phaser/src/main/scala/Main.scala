package lichess

import akka.actor.ActorSystem
import akka.stream.scaladsl._
import reactivemongo.akkastream.cursorProducer
import reactivemongo.api._
import reactivemongo.api.bson._
import reactivemongo.api.bson.collection.BSONCollection
import scala.concurrent.ExecutionContext.Implicits.global
import scala.concurrent.Future

import chess.format.{FEN, Forsyth, Uci}

object Main extends App {

  implicit val system = ActorSystem()

  val mongoUri = "mongodb://localhost:27017"

  // Connect to the database: Must be done only once per application
  val driver = AsyncDriver()
  val parsedUri = MongoConnection.fromString(mongoUri)

  // Database and collections: Get references
  val futureConnection = parsedUri.flatMap(driver.connect(_))
  def db: Future[DB] = futureConnection.flatMap(_.database("puzzler"))
  def puzzleColl = db.map(_.collection("puzzle2"))

  case class Puzzle(id: String, fen: FEN, move: String)

  def read(doc: BSONDocument): Puzzle = {
    for {
      id <- doc.string("_id")
      fen <- doc.string("fen").map(FEN.apply)
      move <- doc.getAsOpt[List[String]]("moves").flatMap(_.headOption)
    } yield Puzzle(id, fen, move)
  } getOrElse sys.error(s"Can't read BSONDocument ${doc.string("_id")}")

  def phaseOf(puzzle: Puzzle): String = {
    for {
      situation <- Forsyth.<<(puzzle.fen)
      uci <- Uci.Move(puzzle.move)
      next <- situation.move(uci).toOption
      board = next.finalizeAfter
    } yield Divider(board)
  } getOrElse sys.error(s"Can't make board for $puzzle")

  def update(coll: BSONCollection, puzzle: Puzzle, phase: String) = {
    // coll.update.one(
    //   BSONDocument("_id" -> puzzle.id),
    //   BSONDocument(
    //     "$pull" -> BSONDocument(
    //       "tags" -> BSONDocument("$elemMatch" -> BSONDocument("$ne" -> phase))
    //     )
    //   )
    // ) flatMap { _ =>
    coll.update.one(
      BSONDocument("_id" -> puzzle.id),
      BSONDocument("$addToSet" -> BSONDocument("tags" -> phase))
    )
  }

  puzzleColl
    .flatMap { coll =>
      coll
        .find(
          BSONDocument(
            "tags" -> BSONDocument(
              "$nin" -> List("opening", "middlegame", "endgame")
            )
          )
        )
        .cursor[BSONDocument]()
        .documentSource()
        .map(read)
        .map(p => p -> phaseOf(p))
        .mapAsyncUnordered(8) { case (p, phase) =>
          update(coll, p, phase)
        }
        .toMat(Sink.ignore)(Keep.right)
        .run()
    }
    .andThen { _ =>
      driver.close()
      system.terminate()
    }
}

// hacked from scalachess
object Divider {

  import chess._

  def apply(board: Board): String = {

    val isOpening = ! {
      majorsAndMinors(board) <= 10 || backrankSparse(board) || mixedness(
        board
      ) > 150
    }

    val isEndGame = !isOpening && majorsAndMinors(board) <= 6

    if (isOpening) "opening"
    else if (isEndGame) "endgame"
    else "middlegame"
  }

  private def majorsAndMinors(board: Board): Int =
    board.pieces.values.foldLeft(0) { (v, p) =>
      if (p.role == Pawn || p.role == King) v else v + 1
    }

  private val backranks =
    List(Pos.whiteBackrank -> Color.White, Pos.blackBackrank -> Color.Black)

  // Sparse back-rank indicates that pieces have been developed
  private def backrankSparse(board: Board): Boolean =
    backranks.exists { case (backrank, color) =>
      backrank.count { pos =>
        board(pos).fold(false)(_ is color)
      } < 4
    }

  private def score(white: Int, black: Int, y: Int): Int =
    (white, black) match {
      case (0, 0) => 0

      case (1, 0) => 1 + (8 - y)
      case (2, 0) => if (y > 2) 2 + (y - 2) else 0
      case (3, 0) => if (y > 1) 3 + (y - 1) else 0
      case (4, 0) =>
        if (y > 1) 3 + (y - 1) else 0 // group of 4 on the homerow = 0

      case (0, 1) => 1 + y
      case (1, 1) => 5 + (3 - y).abs
      case (2, 1) => 4 + y
      case (3, 1) => 5 + y

      case (0, 2) => if (y < 6) 2 + (6 - y) else 0
      case (1, 2) => 4 + (6 - y)
      case (2, 2) => 7

      case (0, 3) => if (y < 7) 3 + (7 - y) else 0
      case (1, 3) => 5 + (6 - y)

      case (0, 4) => if (y < 7) 3 + (7 - y) else 0

      case _ => 0
    }

  private val mixednessRegions: List[List[Pos]] = {
    for {
      y <- Rank.all.take(7)
      x <- File.all.take(7)
    } yield {
      for {
        dy <- 0 to 1
        dx <- 0 to 1
        file <- x.offset(dx)
        rank <- y.offset(dy)
      } yield Pos(file, rank)
    }.toList
  }.toList

  private def mixedness(board: Board): Int = {
    val boardValues = board.pieces.view.mapValues(_ is Color.white)
    mixednessRegions.foldLeft(0) { case (mix, region) =>
      var white = 0
      var black = 0
      region foreach { p =>
        boardValues get p foreach { v =>
          if (v) white = white + 1
          else black = black + 1
        }
      }
      mix + score(white, black, region.head.rank.index + 1)
    }
  }
}
