const fs = require('fs');

// More phonetics for remaining words
const phoneticMap = {
  "laugh": "/lɑːf/",
  "opera": "/ˈɒprə/",
  "better": "/ˈbetə(r)/",
  "model": "/ˈmɒdl/",
  "shout": "/ʃaʊt/",
  "feeling": "/ˈfiːlɪŋ/",
  "huge": "/hjuːdʒ/",
  "hit": "/hɪt/",
  "talent": "/ˈtælənt/",
  "act": "/ækt/",
  "magic": "/ˈmædʒɪk/",
  "shine": "/ʃaɪn/",
  "puzzle": "/ˈpʌzl/",
  "dancer": "/ˈdɑːnsə(r)/",
  "win": "/wɪn/",
  "seed": "/siːd/",
  "earth": "/ɜːθ/",
  "stem": "/stem/",
  "dig": "/dɪɡ/",
  "sunflower": "/ˈsʌnflaʊə(r)/",
  "plant": "/plɑːnt/",
  "dream": "/driːm/",
  "true": "/truː/",
  "come true": "/kʌm truː/",
  "drama": "/ˈdrɑːmə/",
  "fair": "/feə(r)/",
  "horn": "/hɔːn/",
  "dot": "/dɒt/",
  "raindrop": "/ˈreɪndrɒp/",
  "keeper": "/ˈkiːpə(r)/",
  "note": "/nəʊt/",
  "vote": "/vəʊt/",
  "design": "/dɪˈzaɪn/",
  "hometown": "/ˈhəʊmtaʊn/",
  "dressmaker": "/ˈdresmeɪkə(r)/",
  "wrong": "/rɒŋ/",
  "Mr": "/ˈmɪstə(r)/",
  "uniform": "/ˈjuːnɪfɔːm/",
  "robe": "/rəʊb/"
};

const filePath = 'public/data/en/grade4-spring.json';
const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));

let updated = 0;
let missing = [];

data.words.forEach(word => {
  if (!word.phonetic || word.phonetic === '') {
    const lowerWord = word.word.toLowerCase();
    if (phoneticMap[lowerWord]) {
      word.phonetic = phoneticMap[lowerWord];
      updated++;
    } else {
      missing.push(word.word);
    }
  }
});

fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');

console.log(`Updated grade4-spring.json: ${updated} phonetics added`);
if (missing.length > 0) {
  console.log(`Still missing ${missing.length} phonetics:`);
  console.log(missing.join(', '));
} else {
  console.log('All phonetics have been added!');
}
