const puzzleColl = db.puzzle2_puzzle;
const pathColl = db.puzzle2_path;
pathColl.remove({});

const generation = Date.now()

const tiers = [
  ['top', 25 / 100],
  ['all', 100 / 100]
];

const acceptableVoteSelect = {
  vote: {
    $gt: -100
  }
};

const themes = db.puzzle2_puzzle.distinct('themes',{});

function makeTier(theme, tierName, thresholdRatio) {

  const selector = {
    ...acceptableVoteSelect,
    ...(theme ? {themes: theme} : {})
  };

  const nbAcceptablePuzzles = puzzleColl.count(selector);

  if (!nbAcceptablePuzzles) return;

  const nbPuzzles = Math.round(nbAcceptablePuzzles * thresholdRatio);

  const pathLength = Math.max(20, Math.min(100, Math.round(nbPuzzles / 100)));

  const nbRatingBuckets = Math.max(1, Math.min(10, Math.round(nbPuzzles / pathLength / 20)));

  print(`theme: ${theme}, tier: ${tierName}, threshold: ${thresholdRatio}, puzzles: ${nbPuzzles}, path length: ${pathLength}, rating buckets: ${nbRatingBuckets}`);

  const ratingBuckets = db.puzzle2_puzzle.aggregate([{
    $match: selector
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
  }], {
    allowDiskUse: true,
    comment: 'make-paths'
  });

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
    // print(`  ${ratingMin}->${ratingMax} paths: ${paths.length}`);
    paths.forEach((ids, i) => {
      pathColl.insert({
        _id: `${theme || 'any'}_${tierName}_${ratingMin}-${ratingMax}_${generation}_${i}`,
        tier: tierName,
        theme: theme,
        min: ratingMin,
        max: ratingMax,
        ids,
        length: ids.length
      });
    });
  });
}

themes.concat([null]).forEach(theme =>
// ['exposedKing'].forEach(theme =>
  tiers.forEach(([name, threshold]) => makeTier(theme, name, threshold))
);
