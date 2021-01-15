// run this on puzzler DB
// with bin/master-theme.sh

const supergms = new Set([
'DrNykterstein',
'DrDrunkenstein',
'DannyTheDonkey',
'ManWithaVan',
'Bombegranate',
'avalongamemaster',
'Konevlad',
'alireza2003',
'Azerichessss',
'Moose959',
'AnishGiri',
'AnishOnYoutube',
'GMVallejo',
'Vladimirovich9000',
'EvilGenius94',
'BakukaDaku87',
'Wesley_So',
'STL_So',
'gmwesleyso1993',
'RealDavidNavara',
'Dr-BassemAmin',
'gmluke',
'howitzer14',
'Benefactorr',
'IGMGataKamsky',
'dalmatinac101',
'Vladimir201701',
'LiviuDieterNisipeanu',
'jitanu76',
'ArkadijNaiditsch',
'R-Ponomariov',
'athena-pallada',
'Chepursias',
'muisback',
'VerdeNotte',
'KeyzerSose',
'NeverEnough',
'Sasha',
'jlhammer',
].map(n => n.toLowerCase()));

const masterThemesFor = m => { 
  const t = ['master']; 
  if (m.users[1]) t.push('masterVsMaster'); 
  if (m.users.find(u => supergms.has(u._id))) t.push('superGM');
  return t;
}

db.puzzle2_master.find().forEach(m => {
  const themes = masterThemesFor(m);
  db.puzzle2_puzzle.updateOne({_id:m._id},{$addToSet:{themes:{$each:themes}}});
  const plusThemes = themes.map(t => '+' + t);
  db.puzzle2_round.updateOne({_id:'lichess:'+m._id},{$addToSet:{t:{$each:plusThemes}}});
})
