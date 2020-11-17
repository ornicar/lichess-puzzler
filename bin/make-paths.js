const puzzleColl = db.puzzle2_puzzle;
const pathColl = db.puzzle2_path;
pathColl.remove({});

const generation = Date.now()

const nbRatingBuckets = 10;

const pathLength = 100;

const tiers = [
  ['top', 25 / 100],
  ['all', 100 / 100]
];

const acceptableVoteSelect = {
  vote: {
    $gt: -100
  }
};

const nbAcceptablePuzzles = puzzleColl.count(acceptableVoteSelect);

function makeTier(tierName, thresholdRatio) {

  const nbPuzzles = Math.round(nbAcceptablePuzzles * thresholdRatio);

  print(`tier: ${tierName}, threshold: ${thresholdRatio}, puzzles: ${nbPuzzles}`);

  const ratingBuckets = db.puzzle2_puzzle.aggregate([{
    $match: acceptableVoteSelect
  }, {
    $sort: {
      vote: -1
    }
  }, {
    $limit: nbPuzzles
  }, {
    $bucketAuto: {
      groupBy: '$glicko.r',
      buckets: nbRatingBuckets,
      output: {
        puzzles: {
          $addToSet: '$_id'
        }
      }
    }
  }]);
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

  // explodeArray([1..12], 3)
  // [[1, 4, 7, 10], [2, 5, 8, 11], [3, 5, 9, 12]]
  function explodeArray(arr, nb) {
    const res = [];
    for (i = 0; i < nb; i++) res[i] = [];
    for (i in arr) res[i % nb].push(arr[i]);
    return res;
  }

  let bucketNumber = 0;
  ratingBuckets.forEach(bucket => {
    const ratingMin = Math.ceil(bucket._id.min);
    const ratingMax = ++bucketNumber == nbRatingBuckets ? 9999 : Math.floor(bucket._id.max);
    const nbPaths = Math.floor(bucket.puzzles.length / pathLength);
    const puzzles = bucket.puzzles.slice(0, nbPaths * pathLength);
    const paths = explodeArray(puzzles, nbPaths);
    print(`  ${ratingMin}->${ratingMax} paths: ${paths.length}`);
    paths.forEach((ids, i) => {
      pathColl.insert({
        _id: `${generation}_${tierName}_${ratingMin}-${ratingMax}_${i}`,
        tier: tierName,
        min: ratingMin,
        max: ratingMax,
        ids
      });
    });
  });
}

print()
print(`rating buckets: ${nbRatingBuckets}, path length: ${pathLength}`);
print()

tiers.forEach(([name, threshold]) => makeTier(name, threshold));
