db.puzzle2_puzzle.find({vote:1, cp: {$exists:1}},{_id:1, vote:1, cp:1}).forEach(p => {

  const build = db.puzzle2.findOne({_id:p._id},{generator:1});
  
  if (!build) {
    print('Missing build for ' + p._id);
    return;
  }

  const generatorVote =
    // possible rejected mate in X when mate in one available
    build.generator < 24 && p.cp == 999999999 ? -15 : (
      // 40 meganodes
      build.generator < 13 ? -10 : (
        // 0.64 win diff
        build.generator < 22 ? -5 : 2
      )
    );

  print(p._id + ': ' + p.vote + ' -> ' + generatorVote);

  if (p.vote != generatorVote) db.puzzle2_puzzle.update({_id: p._id},{$set:{vote: NumberInt(generatorVote)}});

});
