package lichess

import akka.actor.ActorSystem
import akka.stream.scaladsl._
import chess.format.{ FEN, Forsyth, Uci }
import chess.opening.FullOpening
import reactivemongo.akkastream.cursorProducer
import reactivemongo.api._
import reactivemongo.api.bson._
import reactivemongo.api.bson.collection.BSONCollection
import scala.concurrent.ExecutionContext.Implicits.global
import scala.concurrent.Future

object Main extends App {

  implicit val system = ActorSystem()

  val mongoUri = "mongodb://localhost:27017"

  // Connect to the database: Must be done only once per application
  val driver    = AsyncDriver()
  val parsedUri = MongoConnection.fromString(mongoUri)

  // Database and collections: Get references
  val futureConnection     = parsedUri.flatMap(driver.connect(_))
  def puzzleDb: Future[DB] = futureConnection.flatMap(_.database("puzzler"))
  def puzzleColl           = puzzleDb.map(_.collection("puzzle2_puzzle"))
  def gameDb: Future[DB]   = futureConnection.flatMap(_.database("lichess"))
  def gameColl             = puzzleDb.map(_.collection("game5"))

  case class Puzzle(id: String, fen: FEN, move: String)

  def read(doc: BSONDocument): Puzzle = {
    for {
      id   <- doc.string("_id")
      fen  <- doc.string("fen").map(FEN.apply)
      move <- doc.getAsOpt[String]("line").map(_.takeWhile(' ' !=))
    } yield Puzzle(id, fen, move)
  } getOrElse sys.error(s"Can't read BSONDocument ${doc.string("_id")}")

  def phaseOf(puzzle: Puzzle): String = {
    for {
      situation <- Forsyth.<<(puzzle.fen)
      uci       <- Uci.Move(puzzle.move)
      next      <- situation.move(uci).toOption
      board = next.finalizeAfter
    } yield Divider(board)
  } getOrElse sys.error(s"Can't make board for $puzzle")

  def openingOf(puzzle: Puzzle): Future[FullOpening] = ??? // FullOpeningDB.search

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
      BSONDocument("_id"       -> puzzle.id),
      BSONDocument("$addToSet" -> BSONDocument("themes" -> phase))
    )
  }

  puzzleColl
    .flatMap { coll =>
      coll
        .find(
          BSONDocument(
            "$or" -> BSONArray(
              BSONDocument(
                "themes" -> BSONDocument(
                  "$nin" -> List("opening", "middlegame", "endgame")
                )
              ),
              BSONDocument(
                "opening" -> BSONDocument("$exists" -> false)
              )
            )
          )
        )
        .cursor[BSONDocument]()
        .documentSource()
        .map(read)
        .mapAsyncUnordered(16) { p =>
          openingOf(p) map { opening => (p, phaseOf(p), opening) }
        }
        .mapAsyncUnordered(16) { case (p, phase, opening) =>
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
