#!/bin/sh

perf=blitz
OUT=data/supergm-games-$perf.pgn
rm $OUT

supergms='DrNykterstein DrDrunkenstein DannyTheDonkey ManWithaVan Bombegranate avalongamemaster Konevlad alireza2003 Azerichessss Moose959 AnishGiri AnishOnYoutube GMVallejo Vladimirovich9000 EvilGenius94 BakukaDaku87 Wesley_So STL_So gmwesleyso1993 RealDavidNavara Dr-BassemAmin gmluke howitzer14 Benefactorr IGMGataKamsky dalmatinac101 Vladimir201701 LiviuDieterNisipeanu jitanu76 ArkadijNaiditsch R-Ponomariov athena-pallada Chepursias muisback VerdeNotte KeyzerSose NeverEnough Sasha jlhammer'

for u in $supergms; do
  echo $u
  curl https://lichess.org/api/games/user/$u\?perfType\=$perf\&rated\=true\&analysed\=true\&clocks=false\&evals\=true >> $OUT
done
