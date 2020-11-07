
```
const toMake = id => {p=db.puzzle2.findOne({_id:id}); return `make("${id}", "${p.fen}", "${p.moves.join(' ')}")`}
const toTest = id => `self.assertTrue(cook.test(${toMake(id)}))`
```
