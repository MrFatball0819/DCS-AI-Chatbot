// ==========================================
// 🚀 DCS 戰術 AI 副駕駛 - 純記憶體 WAV 封裝模組 (dsp_processor.js)
// ==========================================
function addWavHeader(pcmBuffer, sampleRate, bitsPerSample, channels) {
    const header = Buffer.alloc(44);
    header.write('RIFF', 0);
    header.writeUInt32LE(36 + pcmBuffer.length, 4);
    header.write('WAVE', 8);
    header.write('fmt ', 12);
    header.writeUInt32LE(16, 16);
    header.writeUInt16LE(1, 20); 
    header.writeUInt16LE(channels, 22);
    header.writeUInt32LE(sampleRate, 24);
    header.writeUInt32LE(sampleRate * channels * (bitsPerSample / 8), 28);
    header.writeUInt16LE(channels * (bitsPerSample / 8), 32);
    header.writeUInt16LE(bitsPerSample, 34);
    header.write('data', 36);
    header.writeUInt32LE(pcmBuffer.length, 40);
    return Buffer.concat([header, pcmBuffer]);
}

function processAudioInMemory(audioChunks) {
    if (!audioChunks || audioChunks.length === 0) return null;

    const rawPcm48kStereo = Buffer.concat(audioChunks);
    const pcm16kMonoLength = Math.floor(rawPcm48kStereo.length / 6); 
    const rawPcm16kMono = Buffer.alloc(pcm16kMonoLength);
    
    let writeIndex = 0;
    let lastLeftSample = 0; 
    const ALPHA = 0.5; 

    for (let i = 0; i < rawPcm48kStereo.length; i += 12) { 
        if (writeIndex + 1 < rawPcm16kMono.length && i + 1 < rawPcm48kStereo.length) {
            let currentLeftSample = rawPcm48kStereo.readInt16LE(i);
            let filteredSample = lastLeftSample + ALPHA * (currentLeftSample - lastLeftSample);
            lastLeftSample = filteredSample; 
            let finalSample = Math.max(-32768, Math.min(32767, Math.floor(filteredSample)));
            rawPcm16kMono.writeInt16LE(finalSample, writeIndex);
            writeIndex += 2;
        }
    }

    // 🚀 返回 100% 純記憶體帶檔頭的 WAV 數據
    return addWavHeader(rawPcm16kMono, 16000, 16, 1);
}

module.exports = { processAudioInMemory };
