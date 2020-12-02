const playColl = db.puzzle2_puzzle;

function randn_bm() {
  let u = 0,
    v = 0;
  while (u === 0) u = Math.random(); //Converting [0,1) to (0,1)
  while (v === 0) v = Math.random();
  return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

playColl.find({
  // 'vote': 1
}, { _id: true }).forEach(p => {
  const vote = Math.round(randn_bm() * 800 + 500);
  playColl.update({_id:p._id}, {$set:{'vote': vote}});
});
