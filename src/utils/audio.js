/**
 * TTS (Text-to-Speech) utility using Web Speech API
 */

let synth = window.speechSynthesis;

/**
 * Speak a word using TTS
 * @param {string} text - The word to speak
 * @param {string} lang - Language code (e.g., 'en-US', 'zh-CN')
 * @param {number} rate - Speech rate (0.1 to 10, default 0.8)
 * @returns {Promise<void>}
 */
export function speak(text, lang = 'en-US', rate = 0.8) {
  return new Promise((resolve, reject) => {
    if (!synth) {
      reject(new Error('Speech synthesis not supported'));
      return;
    }

    // Cancel any ongoing speech
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    utterance.rate = rate;
    utterance.pitch = 1;
    utterance.volume = 1;

    utterance.onend = () => resolve();
    utterance.onerror = (event) => reject(event.error);

    synth.speak(utterance);
  });
}

/**
 * Speak a word in English
 * @param {string} word - The English word
 * @param {number} rate - Speech rate
 */
export function speakEnglish(word, rate = 0.8) {
  return speak(word, 'en-US', rate);
}

/**
 * Speak a word in Chinese
 * @param {string} word - The Chinese word
 * @param {number} rate - Speech rate
 */
export function speakChinese(word, rate = 0.8) {
  return speak(word, 'zh-CN', rate);
}

/**
 * Check if speech synthesis is supported
 * @returns {boolean}
 */
export function isSpeechSupported() {
  return 'speechSynthesis' in window;
}

/**
 * Get available voices for a language
 * @param {string} lang - Language code
 * @returns {SpeechSynthesisVoice[]}
 */
export function getVoices(lang) {
  return synth.getVoices().filter(voice => voice.lang.startsWith(lang));
}
