// run on lichess DB after importing puzzles and rounds into it
// with master-theme.sh
db.puzzle2_puzzle.aggregate([
  {$lookup:{from:'game5',as:'game',localField:'gameId',foreignField:'_id'}},
  {$unwind:'$game'},
  {$project:{'game.us':1}},
  {$unwind:'$game.us'},
  {$lookup:{
    from:'user4',
    as:'users',
    let:{us:'$game.us'},
    pipeline:[
      {$match:{$expr:{$and:[{$eq:['$_id','$$us']},{$ne:['$title','BOT']}]}}},
      {$match:{title:{$exists:1}}},
      {$project:{title:1}}
    ]}},
  {$unwind:'$users'},
  {$project:{users:1}},
  {$group:{_id:'$_id',users:{$push:'$users'}}},
  {$merge:{into:{db:'puzzler',coll:'puzzle2_master'},whenMatched:'keepExisting',whenNotMatched:'insert'}}
]);
