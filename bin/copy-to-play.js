const buildColl = db.puzzle2;
const playColl = db.puzzle2_puzzle;

const blacklist = 'aZA2E DGRGq IAmuX 7kxXk X6Ouz vlmzA QPlRQ 7aYIM 4QK8g G9HVD TYqQg w7B1B 5Zl9D AyVYO LDH9c CDMr8 aRxWY pMCI3 VyiLO u0Vt9 SSFCq 1OyI9 iumYR DhEGo ScWiu wLF5p xgDL7 OQ9LQ OShoC h7wfU cWZ8d l1uIK 8hpbj jXyLb 4h7SU lgBIK p5FMZ y1HZz OOtcn NZWZu YaUhp W2jar aNMez pDlsC 3Qbbp 8kqIx atkK0 9aKCA 6n1uD QRdHy 4rhYe KuRZI FVN3a WN5PD nunoF WVlBd hOQyE JOGHR kASdu 6DuKA QToeY txDP4 vhqnu InyAN mSUWB mwzRY DHvnF C0cQ8 5Rbom Ba7lO 409sk KziQ9 APPqb BVX2q iZWer sv2Ct fSGr0 iLKHO dPQeJ p4Dbb 9MaEh svVdP fBW6z cpOui OO6nd rUphz yb8ck S2WE9 YOvx8 2L0jc QXHEv m1YnI pbvQR WuH0P rnFT3 VjxTq qPkYQ OivtA Xi0rf HmydS Y9Ysz znOWn nsOm0 d7SzA JsL3K t8dvC Tpc7S 5asD7 Phs60 vPsaP Qc1hU fpH3L FkEGA ovtmM ZpFor 1hZkW W4evP x2uTL pHycY YauPY g8Q75 U62fH Pd8R0 0enn7 Uakgh xn9rj TusZS Ivq97 6apoo zXLcf l7jb9 Fyfa3 aVW7x 9CSGg Hshg2 Zi5oT k56iK nrNaZ 5LCGC HrwLw 7PBgr Nbofc WBmM9 Y9z3C pd5Vp ir6lQ owbsF QPHjS b6ry9 5BShd TGDOW ofStc CMT66 6c4PV NuI2H 6kdL4 Czx2X hRo20 snDwA veQOV cDJ6h 3PeGY L7RF5 K9XFw 81H8U hZKrp 9NAdj Bfnoq SZg6h 4OvRg AUtLE wegTm gz52d hKpKx 9Xx2g iBIKW trlSC f6BIr OPRKw kW1uP IQfNf d1c8H D8Z3u HKRiC Pjys4 LGF4q n0R9J n8br9 ipMsK Ad2Bz 24Va7 t8PDl QGU2W fmQFn pRwrk W48oo Q1f2B ZzgN2 onCeq d8s4l LzQoV 1NHno rBnOe d9Ik5 3HoLz Ent4w 3p5ZP YubAe q4buo ZGgiN BMbRr DrHs4 SrQob fP9sX auNwy t89Kh vP0eZ 0Jcsf 1PIdq aVmoJ olnqN U4mq3 AmNj3 u60qZ Vnznu 25o87 Q9LBH F4UuY CkeKA HecB7 edLRv YtCQO v0091 SG7Ox 09daJ AYlUM EFcTj IPfPk CAwlF ERVwp 9l6AZ 6sIfe ydqBO F27wA RM8D1 8snLR tSYk3 tck6M ytgMW 6r6Rq 5kP48 8sGha GxjHe nBqNu aM13i GkoOI WKlAt 510MZ vfV9N pFs3j IlZcF a0cLv dzJUh jBUOV EWLP3 LWSmF 8HWtb fVKHL r7hul YnVVm kAuwS WUV7i 8fEuU Byzcx aZA2E IKz7V j80ir A6r8E ozc6y VgI0M 7ssWc iI3P6 iEyIG bfKjA SzxK5 9ICZc tS4ox Z5Ryd 4JolL kquFa 2mHPh wug0H Zidvw pRscU APfWy BC2gt u3wOk gDEwQ CZ9rS 5cC75 remGb KGjV6 WHa8W zaDI7 hdt4j cceXB Q2dln BaC6K irheS XclY5 qoiZt 2m4td ZcWmW CJkK9 PPC5a 9qRPl uNb25 SfjYT LKVyJ QECPJ K5GDu 2umhS GLILQ tkB4F FIQf4 bEtXR rAbtJ NwdPf HPGVx nzbaO OM0hh iIoTG 58MP5 irUMS UAqLr OKA9Z LlmiC q9L4s 9nNSs fFZI3 piRpi eQ9K7 Yzyrn 15AlC 2uZRP 4W7Ln NsLdd FBjv2 xcTjo 8Xfzk o3ZqX BqzGx W11w4 6UxWy KasIu TCVnf GZSz2 X0eLF lxVRc q89NA mB5mQ hGzMC WcfK7 YpmqT rUzVm 4WFF9 4dPF4 ypuV0 HI9nh RmPw3 5vyhs ImVpx u7Vy5 dqcW0 i5Y0X cDyUn klZZp HS3ai'.split(' ');

buildColl.remove({_id:{$in:blacklist}});
playColl.remove({_id:{$in:blacklist}});

buffer = [];

function process(buf) {
  const existingIds = new Set(playColl.distinct('_id', {_id:{$in:buf.map(p => p._id)}}));
  const missing = buf.filter(p => !existingIds.has(p._id)).map(p => ({
    _id: p._id,
    gameId: p.gameId,
    fen: p.fen,
    themes: [],
    glicko: {
      r: 1500,
      d: 500,
      v: 0.09
    },
    plays: NumberInt(0),
    vote: 1,
    vu: NumberInt(10),
    vd: NumberInt(0),
    line: p.moves.join(' '),
    cp: p.cp
  }));
  if (missing.length) playColl.insertMany(missing, {ordered:false});
}

buildColl.find({'review.approved':{$ne:false},_id:{$nin:blacklist}}).forEach(p => {
  if (p.moves.length < 2) return;
  buffer.push(p);
  if (buffer.length >= 1000) {
    process(buffer);
    buffer = [];
  }
});

process(buffer);
