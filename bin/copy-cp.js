const buildColl = db.puzzle2;
const playColl = db.puzzle2_puzzle;

playColl.find({cp:{$exists:false}}, {_id:true}).forEach(p => {
  const b = buildColl.findOne({_id:p._id,cp:{$exists:true}}, {cp:true});
  if (b) playColl.update({_id:p._id},{$set:{cp: b.cp}});
});
