import { MdHealthAndSafety } from "react-icons/md";
import { useRTVIClientMediaTrack } from "@pipecat-ai/client-react";
import { useState, useEffect, useRef } from "react";

// No props needed for this component
export default function AgentVisualiser() {
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [isAudioActive, setIsAudioActive] = useState<boolean>(false);

  const botAudioTrack = useRTVIClientMediaTrack("audio", "bot");

  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationRef = useRef<number | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Set up audio analysis when track is available
  useEffect(() => {
    if (!botAudioTrack) {
      setIsAudioActive(false);
      return;
    }

    // Create a MediaStream from the MediaStreamTrack
    const stream = new MediaStream([botAudioTrack]);
    streamRef.current = stream;
    setIsAudioActive(true);

    // Set up audio context and analyzer
    const audioContext = new AudioContext();
    audioContextRef.current = audioContext;
    const analyser = audioContext.createAnalyser();
    analyserRef.current = analyser;

    analyser.fftSize = 256;
    const source = audioContext.createMediaStreamSource(stream);
    source.connect(analyser);

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    // Function to analyze audio and update level
    const analyzeAudio = () => {
      if (!analyserRef.current) return;

      analyserRef.current.getByteFrequencyData(dataArray);

      // Calculate average volume level
      const sum = dataArray.reduce((acc, value) => acc + value, 0);
      const average = sum / dataArray.length;
      const normalizedLevel = average / 255; // Normalize to 0-1 range

      // Scale the level for better visual effect (0.05 minimum scale + up to 0.1 additional scale)
      setAudioLevel(normalizedLevel * 1.4);
      animationRef.current = requestAnimationFrame(analyzeAudio);
    };

    analyzeAudio();

    // Cleanup
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      setIsAudioActive(false);
    };
  }, [botAudioTrack]);

  return (
    <div className="flex justify-center align-middle self-center relative">
      <MdHealthAndSafety className="text-aws-orange h-full w-16 self-center absolute z-10" />
      <div
        className="bg-white w-28 h-28 shadow-md rounded-full flex align-middle justify-center transition-transform"
        style={isAudioActive && audioLevel > 0 ? {
          transform: `scale(${1 + audioLevel})`,
          transition: 'transform 0.1s ease-out'
        } : {
          animation: 'pulse 3s ease-in-out infinite',
        }}
      />
    </div>
  )
}
