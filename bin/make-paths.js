const pathColl = db.puzzle2_path;
pathColl.remove({});

const ratingBuckets = db.puzzle2_puzzle.aggregate([{
    $match: {
      vote: {
        $gt: -100
      }
    }
  }, {
    $sort: {
      vote: -1
    }
  }, {
    $bucketAuto: {
      groupBy: '$glicko.r',
      buckets: 10,
      output: {
        puzzles: {
          // $push: '$_id'
          $push: {
            id: '$_id',
            vote: '$vote'
          }
        }
      }
    }
  }, {
    $unwind: '$puzzles'
  }, {
    $sort: {
      'puzzles.vote': -1
    }
  },
  {
    $group: {
      _id: '$_id',
      puzzles: {
        $push: '$puzzles.id'
      }
    }
  }
]);
/*
min: 600,                max: 1100.4181703369281, puzzles: 7483
min: 1100.4181703369281, max: 1254.6172196150442, puzzles: 7483
min: 1254.6172196150442, max: 1365.2320078716336, puzzles: 7483
min: 1365.2320078716336, max: 1460.879583910132,  puzzles: 7483
min: 1460.879583910132 , max: 1550.0613267713964, puzzles: 7483
min: 1550.0613267713964, max: 1638.4124565085565, puzzles: 7483
min: 1638.4124565085565, max: 1733.2716721830002, puzzles: 7483
min: 1733.2716721830002, max: 1843.5956673443525, puzzles: 7483
min: 1843.5956673443525, max: 1996.2274568220062, puzzles: 7483
min: 1996.2274568220062, max: 2977.877271680098,  puzzles: 7484
*/

const pathLength = 100;

// explodeArray([a, b, c, d, e, g, h, i, j], 3)
// [[a, d, h], [b, e, i], [c, g, j]]
function explodeArray(arr, nb) {
  const res = [];
  for (i = 0; i < nb; i++) res[i] = [];
  for (i in arr) res[i % nb].push(arr[i]);
  return res;
}

ratingBuckets.forEach(bucket => {
  const nbPaths = Math.floor(bucket.puzzles.length / pathLength);
  const puzzles = bucket.puzzles.slice(0, nbPaths * pathLength);
  const paths = explodeArray(puzzles, nbPaths);
  paths.forEach((ids, i) => {
    const [min, max] = [Math.ceil(bucket._id.min), Math.floor(bucket._id.max)];
    pathColl.insert({
      _id: `${min}-${max}_${i}`,
      min,
      max,
      ids
    });
  });
});
