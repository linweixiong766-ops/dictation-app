#!/usr/bin/env python3
"""
下载所有拼音音频
从 https://img.zdic.net/audio/zd/py/ 下载
"""

import os
import urllib.request
import urllib.parse

# 基础URL
BASE_URL = "https://img.zdic.net/audio/zd/py"

# 输出目录
OUTPUT_DIR = "public/audio/pinyin/all-pinyin"

# 所有拼音列表
ALL_PINYIN = [
    # 零声母带调符号版
    "ā", "á", "ǎ", "à",
    "ō", "ó", "ǒ", "ò",
    "ē", "é", "ě", "è",
    "ēr", "ér", "ěr", "èr",
    "āi", "ái", "ǎi", "ài",
    "ēi", "éi", "ěi", "èi",
    "āo", "áo", "ǎo", "ào",
    "ōu", "óu", "ǒu", "òu",
    "ān", "án", "ǎn", "àn",
    "ēn", "én", "ěn", "èn",
    "āng", "áng", "ǎng", "àng",
    "ēng", "éng", "ěng", "èng",
    "ī", "í", "ǐ", "ì",
    "ū", "ú", "ǔ", "ù",
    "ǖ", "ǘ", "ǚ", "ǜ",

    # b组带调
    "bā", "bá", "bǎ", "bà",
    "bāi", "bái", "bǎi", "bài",
    "bān", "bán", "bǎn", "bàn",
    "bāng", "báng", "bǎng", "bàng",
    "bāo", "báo", "bǎo", "bào",
    "bēi", "béi", "běi", "bèi",
    "bēn", "bén", "běn", "bèn",
    "bēng", "béng", "běng", "bèng",
    "bī", "bí", "bǐ", "bì",
    "biān", "bián", "biǎn", "biàn",
    "biāo", "biáo", "biǎo", "biào",
    "biē", "bié", "biě", "biè",
    "bīn", "bín", "bǐn", "bìn",
    "bīng", "bíng", "bǐng", "bìng",
    "bō", "bó", "bǒ", "bò",
    "bū", "bú", "bǔ", "bù",

    # p组带调
    "pā", "pá", "pǎ", "pà",
    "pāi", "pái", "pǎi", "pài",
    "pān", "pán", "pǎn", "pàn",
    "pāng", "páng", "pǎng", "pàng",
    "pāo", "páo", "pǎo", "pào",
    "pēi", "péi", "pěi", "pèi",
    "pēn", "pén", "pěn", "pèn",
    "pēng", "péng", "pěng", "pèng",
    "pī", "pí", "pǐ", "pì",
    "piān", "pián", "piǎn", "piàn",
    "piāo", "piáo", "piǎo", "piào",
    "piē", "pié", "piě", "piè",
    "pīn", "pín", "pǐn", "pìn",
    "pīng", "píng", "pǐng", "pìng",
    "pō", "pó", "pǒ", "pò",
    "pōu", "póu", "pǒu", "pòu",
    "pū", "pú", "pǔ", "pù",

    # m组带调
    "mā", "má", "mǎ", "mà",
    "māi", "mái", "mǎi", "mài",
    "mān", "mán", "mǎn", "màn",
    "māng", "máng", "mǎng", "màng",
    "māo", "máo", "mǎo", "mào",
    "mēi", "méi", "měi", "mèi",
    "mēn", "mén", "měn", "mèn",
    "mēng", "méng", "měng", "mèng",
    "mī", "mí", "mǐ", "mì",
    "miān", "mián", "miǎn", "miàn",
    "miāo", "miáo", "miǎo", "miào",
    "miē", "mié", "miě", "miè",
    "mīn", "mín", "mǐn", "mìn",
    "mīng", "míng", "mǐng", "mìng",
    "mō", "mó", "mǒ", "mò",
    "mōu", "móu", "mǒu", "mòu",
    "mū", "mú", "mǔ", "mù",

    # f组带调
    "fā", "fá", "fǎ", "fà",
    "fān", "fán", "fǎn", "fàn",
    "fāng", "fáng", "fǎng", "fàng",
    "fēi", "féi", "fěi", "fèi",
    "fēn", "fén", "fěn", "fèn",
    "fēng", "féng", "fěng", "fèng",
    "fō", "fó", "fǒ", "fò",
    "fōu", "fóu", "fǒu", "fòu",
    "fū", "fú", "fǔ", "fù",

    # d组带调
    "dā", "dá", "dǎ", "dà",
    "dāi", "dái", "dǎi", "dài",
    "dān", "dán", "dǎn", "dàn",
    "dāng", "dáng", "dǎng", "dàng",
    "dāo", "dáo", "dǎo", "dào",
    "dē", "dé", "dě", "dè",
    "dēi", "déi", "děi",
    "dēng", "déng", "děng", "dèng",
    "dī", "dí", "dǐ", "dì",
    "diān", "dián", "diǎn", "diàn",
    "diāo", "diáo", "diǎo", "diào",
    "diē", "dié", "diě", "diè",
    "dīng", "díng", "dǐng", "dìng",
    "diū", "diú", "diǔ", "diù",
    "dōng", "dóng", "dǒng", "dòng",
    "dōu", "dóu", "dǒu", "dòu",
    "dū", "dú", "dǔ", "dù",
    "duān", "duán", "duǎn", "duàn",
    "duī", "duí", "duǐ", "duì",
    "dūn", "dún", "dǔn", "dùn",
    "duō", "duó", "duǒ", "duò",

    # t组带调
    "tā", "tá", "tǎ", "tà",
    "tāi", "tái", "tǎi", "tài",
    "tān", "tán", "tǎn", "tàn",
    "tāng", "táng", "tǎng", "tàng",
    "tāo", "táo", "tǎo", "tào",
    "tē", "té", "tě", "tè",
    "tēng", "téng", "těng", "tèng",
    "tī", "tí", "tǐ", "tì",
    "tiān", "tián", "tiǎn", "tiàn",
    "tiāo", "tiáo", "tiǎo", "tiào",
    "tiē", "tié", "tiě", "tiè",
    "tīng", "tíng", "tǐng", "tìng",
    "tōng", "tóng", "tǒng", "tòng",
    "tōu", "tóu", "tǒu", "tòu",
    "tū", "tú", "tǔ", "tù",
    "tuān", "tuán", "tuǎn", "tuàn",
    "tuī", "tuí", "tuǐ", "tuì",
    "tūn", "tún", "tǔn", "tùn",
    "tuō", "tuó", "tuǒ", "tuò",

    # n组带调
    "nā", "ná", "nǎ", "nà",
    "nāi", "nái", "nǎi", "nài",
    "nān", "nán", "nǎn", "nàn",
    "nāng", "náng", "nǎng", "nàng",
    "nāo", "náo", "nǎo", "nào",
    "nē", "né", "ně", "nè",
    "nēi", "néi", "něi", "nèi",
    "nēn", "nén", "něn", "nèn",
    "nēng", "néng", "něng", "nèng",
    "nī", "ní", "nǐ", "nì",
    "niān", "nián", "niǎn", "niàn",
    "niāo", "niáo", "niǎo", "niào",
    "niē", "nié", "niě", "niè",
    "nīn", "nín", "nǐn", "nìn",
    "nīng", "níng", "nǐng", "nìng",
    "niū", "niú", "niǔ", "niù",
    "nōng", "nóng", "nǒng", "nòng",
    "nōu", "nóu", "nǒu", "nòu",
    "nū", "nú", "nǔ", "nù",
    "nǖ", "nǘ", "nǚ", "nǜ",
    "nuān", "nuán", "nuǎn", "nuàn",
    "nüē", "nüé", "nüě", "nüè",
    "nuō", "nuó", "nuǒ", "nuò",

    # l组带调
    "lā", "lá", "lǎ", "là",
    "lāi", "lái", "lǎi", "lài",
    "lān", "lán", "lǎn", "làn",
    "lāng", "láng", "lǎng", "làng",
    "lāo", "láo", "lǎo", "lào",
    "lē", "lé", "lě", "lè",
    "lēi", "léi", "lěi", "lèi",
    "lēng", "léng", "lěng", "lèng",
    "lī", "lí", "lǐ", "lì",
    "liān", "lián", "liǎn", "liàn",
    "liāo", "liáo", "liǎo", "liào",
    "liē", "lié", "liě", "liè",
    "līn", "lín", "lǐn", "lìn",
    "līng", "líng", "lǐng", "lìng",
    "liū", "liú", "liǔ", "liù",
    "lōng", "lóng", "lǒng", "lòng",
    "lōu", "lóu", "lǒu", "lòu",
    "lū", "lú", "lǔ", "lù",
    "luān", "luán", "luǎn", "luàn",
    "lǖ", "lǘ", "lǚ", "lǜ",
    "lüē", "lüé", "lüě", "lüè",
    "luō", "luó", "luǒ", "luò",

    # g组带调
    "gā", "gá", "gǎ", "gà",
    "gāi", "gái", "gǎi", "gài",
    "gān", "gán", "gǎn", "gàn",
    "gāng", "gáng", "gǎng", "gàng",
    "gāo", "gáo", "gǎo", "gào",
    "gē", "gé", "gě", "gè",
    "gēi", "géi", "gěi",
    "gēng", "géng", "gěng", "gèng",
    "gōng", "góng", "gǒng", "gòng",
    "gōu", "góu", "gǒu", "gòu",
    "gū", "gú", "gǔ", "gù",
    "guā", "guá", "guǎ", "guà",
    "guāi", "guái", "guǎi", "guài",
    "guān", "guán", "guǎn", "guàn",
    "guāng", "guáng", "guǎng", "guàng",
    "guī", "guí", "guǐ", "guì",
    "gūn", "gún", "gǔn", "gùn",
    "guō", "guó", "guǒ", "guò",

    # k组带调
    "kā", "ká", "kǎ", "kà",
    "kāi", "kái", "kǎi", "kài",
    "kān", "kán", "kǎn", "kàn",
    "kāng", "káng", "kǎng", "kàng",
    "kāo", "káo", "kǎo", "kào",
    "kē", "ké", "kě", "kè",
    "kēn", "kén", "kěn", "kèn",
    "kēng", "kéng", "kěng", "kèng",
    "kōng", "kóng", "kǒng", "kòng",
    "kōu", "kóu", "kǒu", "kòu",
    "kū", "kú", "kǔ", "kù",
    "kuā", "kuá", "kuǎ", "kuà",
    "kuāi", "kuái", "kuǎi", "kuài",
    "kuān", "kuán", "kuǎn", "kuàn",
    "kuāng", "kuáng", "kuǎng", "kuàng",
    "kuī", "kuí", "kuǐ", "kuì",
    "kūn", "kún", "kǔn", "kùn",
    "kuō", "kuó", "kuǒ", "kuò",

    # h组带调
    "hā", "há", "hǎ", "hà",
    "hāi", "hái", "hǎi", "hài",
    "hān", "hán", "hǎn", "hàn",
    "hāng", "háng", "hǎng", "hàng",
    "hāo", "háo", "hǎo", "hào",
    "hē", "hé", "hě", "hè",
    "hēi", "héi", "hěi", "hèi",
    "hēn", "hén", "hěn", "hèn",
    "hēng", "héng", "hěng", "hèng",
    "hōng", "hóng", "hǒng", "hòng",
    "hōu", "hóu", "hǒu", "hòu",
    "hū", "hú", "hǔ", "hù",
    "huā", "huá", "huǎ", "huà",
    "huāi", "huái", "huǎi", "huài",
    "huān", "huán", "huǎn", "huàn",
    "huāng", "huáng", "huǎng", "huàng",
    "huī", "huí", "huǐ", "huì",
    "hūn", "hún", "hǔn", "hùn",
    "huō", "huó", "huǒ", "huò",

    # zh组带调
    "zhā", "zhá", "zhǎ", "zhà",
    "zhāi", "zhái", "zhǎi", "zhài",
    "zhān", "zhán", "zhǎn", "zhàn",
    "zhāng", "zhǎng", "zhàng",
    "zhāo", "zhǎo", "zhào",
    "zhē", "zhé", "zhě", "zhè",
    "zhēi", "zhéi", "zhěi", "zhèi",
    "zhēn", "zhén", "zhěn", "zhèn",
    "zhēng", "zhěng", "zhèng",
    "zhōng", "zhǒng", "zhòng",
    "zhōu", "zhóu", "zhǒu", "zhòu",
    "zhū", "zhú", "zhǔ", "zhù",
    "zhuā", "zhuá", "zhuǎ", "zhuà",
    "zhuāi", "zhuái", "zhuǎi", "zhuài",
    "zhuān", "zhuán", "zhuǎn", "zhuàn",
    "zhuāng", "zhuáng", "zhuǎng", "zhuàng",
    "zhuī", "zhuí", "zhuǐ", "zhuì",
    "zhūn", "zhún", "zhǔn", "zhùn",
    "zhuō", "zhuó", "zhuǒ", "zhuò",

    # ch组带调
    "chā", "chá", "chǎ", "chà",
    "chāi", "chái", "chǎi", "chài",
    "chān", "chán", "chǎn", "chàn",
    "chāng", "cháng", "chǎng", "chàng",
    "chāo", "cháo", "chǎo", "chào",
    "chē", "ché", "chě", "chè",
    "chēn", "chén", "chěn", "chèn",
    "chēng", "chéng", "chěng", "chèng",
    "chōng", "chóng", "chǒng", "chòng",
    "chōu", "chóu", "chǒu", "chòu",
    "chū", "chú", "chǔ", "chù",
    "chuā", "chuá", "chuǎ", "chuà",
    "chuāi", "chuái", "chuǎi", "chuài",
    "chuān", "chuán", "chuǎn", "chuàn",
    "chuāng", "chuáng", "chuǎng", "chuàng",
    "chuī", "chuí", "chuǐ", "chuì",
    "chūn", "chún", "chǔn", "chùn",
    "chuō", "chuó", "chuǒ", "chuò",

    # sh组带调
    "shā", "shá", "shǎ", "shà",
    "shāi", "shái", "shǎi", "shài",
    "shān", "shán", "shǎn", "shàn",
    "shāng", "sháng", "shǎng", "shàng",
    "shāo", "sháo", "shǎo", "shào",
    "shē", "shé", "shě", "shè",
    "shēi", "shéi", "shěi", "shèi",
    "shēn", "shén", "shěn", "shèn",
    "shēng", "shéng", "shěng", "shèng",
    "shōu", "shóu", "shǒu", "shòu",
    "shū", "shú", "shǔ", "shù",
    "shuā", "shuá", "shuǎ", "shuà",
    "shuāi", "shuái", "shuǎi", "shuài",
    "shuān", "shuán", "shuǎn", "shuàn",
    "shuāng", "shuáng", "shuǎng", "shuàng",
    "shuī", "shuí", "shuǐ", "shuì",
    "shūn", "shún", "shǔn", "shùn",
    "shuō", "shuó", "shuǒ", "shuò",

    # r组带调
    "rān", "rán", "rǎn", "ràn",
    "rāng", "ráng", "rǎng", "ràng",
    "rāo", "ráo", "rǎo", "rào",
    "rē", "ré", "rě", "rè",
    "rēn", "rén", "rěn", "rèn",
    "rēng", "réng", "rěng", "rèng",
    "rī", "rí", "rǐ", "rì",
    "rōng", "róng", "rǒng", "ròng",
    "rōu", "róu", "rǒu", "ròu",
    "rū", "rú", "rǔ", "rù",
    "ruān", "ruán", "ruǎn", "ruàn",
    "ruī", "ruí", "ruǐ", "ruì",
    "rūn", "rún", "rǔn", "rùn",
    "ruō", "ruó", "ruǒ", "ruò",

    # z组带调
    "zā", "zá", "zǎ", "zà",
    "zāi", "zái", "zǎi", "zài",
    "zān", "zán", "zǎn", "zàn",
    "zāng", "záng", "zǎng", "zàng",
    "zāo", "záo", "zǎo", "zào",
    "zē", "zé", "zě", "zè",
    "zēi", "zéi", "zěi", "zèi",
    "zēn", "zén", "zěn", "zèn",
    "zēng", "zéng", "zěng", "zèng",
    "zōng", "zóng", "zǒng", "zòng",
    "zōu", "zóu", "zǒu", "zòu",
    "zū", "zú", "zǔ", "zù",
    "zuān", "zuán", "zuǎn", "zuàn",
    "zuī", "zuí", "zuǐ", "zuì",
    "zūn", "zún", "zǔn", "zùn",
    "zuō", "zuó", "zuǒ", "zuò",

    # c组带调
    "cā", "cá", "cǎ", "cà",
    "cāi", "cái", "cǎi", "cài",
    "cān", "cán", "cǎn", "càn",
    "cāng", "cáng", "cǎng", "càng",
    "cāo", "cáo", "cǎo", "cào",
    "cē", "cé", "cě", "cè",
    "cēn", "cén", "cěn", "cèn",
    "cēng", "céng", "cěng", "cèng",
    "cōng", "cóng", "cǒng", "còng",
    "cōu", "cóu", "cǒu", "còu",
    "cū", "cú", "cǔ", "cù",
    "cuān", "cuán", "cuǎn", "cuàn",
    "cuī", "cuí", "cuǐ", "cuì",
    "cūn", "cún", "cǔn", "cùn",
    "cuō", "cuó", "cuǒ", "cuò",

    # s组带调
    "sā", "sá", "sǎ", "sà",
    "sāi", "sái", "sǎi", "sài",
    "sān", "sán", "sǎn", "sàn",
    "sāng", "sáng", "sǎng", "sàng",
    "sāo", "sáo", "sǎo", "sào",
    "sē", "sé", "sě", "sè",
    "sēn", "sén", "sěn", "sèn",
    "sēng", "séng", "sěng", "sèng",
    "sōng", "sóng", "sǒng", "sòng",
    "sōu", "sóu", "sǒu", "sòu",
    "sū", "sú", "sǔ", "sù",
    "suān", "suán", "suǎn", "suàn",
    "suī", "suí", "suǐ", "suì",
    "sūn", "sún", "sǔn", "sùn",
    "suō", "suó", "suǒ", "suò",

    # j组带调
    "jī", "jí", "jǐ", "jì",
    "jiā", "jiá", "jiǎ", "jià",
    "jiān", "jián", "jiǎn", "jiàn",
    "jiāng", "jiáng", "jiǎng", "jiàng",
    "jiāo", "jiáo", "jiǎo", "jiào",
    "jiē", "jié", "jiě", "jiè",
    "jīn", "jín", "jǐn", "jìn",
    "jīng", "jíng", "jǐng", "jìng",
    "jiū", "jiú", "jiǔ", "jiù",
    "jiōng", "jióng", "jiǒng", "jiòng",
    "jū", "jú", "jǔ", "jù",
    "juān", "juán", "juǎn", "juàn",
    "juē", "jué", "juě", "juè",
    "jūn", "jún", "jǔn", "jùn",

    # q组带调
    "qī", "qí", "qǐ", "qì",
    "qiā", "qiá", "qiǎ", "qià",
    "qiān", "qián", "qiǎn", "qiàn",
    "qiāng", "qiáng", "qiǎng", "qiàng",
    "qiāo", "qiáo", "qiǎo", "qiào",
    "qiē", "qié", "qiě", "qiè",
    "qīn", "qín", "qǐn", "qìn",
    "qīng", "qíng", "qǐng", "qìng",
    "qiū", "qiú", "qiǔ", "qiù",
    "qiōng", "qióng", "qiǒng", "qiòng",
    "qū", "qú", "qǔ", "qù",
    "quān", "quán", "quǎn", "quàn",
    "quē", "qué", "quě", "què",
    "qūn", "qún", "qǔn", "qùn",

    # x组带调
    "xī", "xí", "xǐ", "xì",
    "xiā", "xiá", "xiǎ", "xià",
    "xiān", "xián", "xiǎn", "xiàn",
    "xiāng", "xiáng", "xiǎng", "xiàng",
    "xiāo", "xiáo", "xiǎo", "xiào",
    "xiē", "xié", "xiě", "xiè",
    "xīn", "xín", "xǐn", "xìn",
    "xīng", "xíng", "xǐng", "xìng",
    "xiū", "xiú", "xiǔ", "xiù",
    "xiōng", "xióng", "xiǒng", "xiòng",
    "xū", "xú", "xǔ", "xù",
    "xuān", "xuán", "xuǎn", "xuàn",
    "xuē", "xué", "xuě", "xuè",
    "xūn", "xún", "xǔn", "xùn",

    # 整体认读音节带调符号版
    "zhī", "zhí", "zhǐ", "zhì",
    "chī", "chí", "chǐ", "chì",
    "shī", "shí", "shǐ", "shì",
    "rī", "rí", "rǐ", "rì",
    "zī", "zí", "zǐ", "zì",
    "cī", "cí", "cǐ", "cì",
    "sī", "sí", "sǐ", "sì",
    "yī", "yí", "yǐ", "yì",
    "wū", "wú", "wǔ", "wù",
    "yū", "yú", "yǔ", "yù",
    "yē", "yé", "yě", "yè",
    "yuē", "yué", "yuě", "yuè",
    "yuān", "yuán", "yuǎn", "yuàn",
    "yīn", "yín", "yǐn", "yìn",
    "yūn", "yún", "yǔn", "yùn",
    "yīng", "yíng", "yǐng", "yìng",
]

def download_file(url, output_path):
    """下载文件"""
    try:
        # URL编码
        encoded_url = urllib.parse.quote(url, safe=':/')
        urllib.request.urlretrieve(encoded_url, output_path)
        return True
    except Exception as e:
        return False

def main():
    print("开始下载所有拼音音频...")

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    success = 0
    failed = 0
    skipped = 0
    total = len(ALL_PINYIN)

    for pinyin in ALL_PINYIN:
        # 构建URL和输出路径
        url = f"{BASE_URL}/{pinyin}.mp3"

        # 生成文件名（去掉声调符号，保留字母和声调数字）
        # 这里我们直接用带声调的拼音作为文件名
        filename = f"{pinyin}.mp3"
        output_path = os.path.join(OUTPUT_DIR, filename)

        # 检查文件是否已存在
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            skipped += 1
            continue

        print(f"  {pinyin}...", end=" ", flush=True)

        if download_file(url, output_path):
            # 检查文件大小
            size = os.path.getsize(output_path)
            if size > 1000:
                print(f"OK ({size} bytes)")
                success += 1
            else:
                print(f"FAILED (too small: {size} bytes)")
                os.remove(output_path)
                failed += 1
        else:
            print("FAILED")
            failed += 1

    print(f"\n{'='*50}")
    print(f"下载完成！")
    print(f"总计: {total}, 成功: {success}, 失败: {failed}, 跳过: {skipped}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
