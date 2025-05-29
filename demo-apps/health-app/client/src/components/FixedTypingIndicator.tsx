import { Box, Paper, Typography, keyframes } from '@mui/material';
import { RTVIEvent } from '@pipecat-ai/client-js';
import { useRTVIClientEvent } from '@pipecat-ai/client-react';
import { useCallback, useState } from 'react';

const blink = keyframes`
  0% { opacity: 0.2; }
  20% { opacity: 1; }
  100% { opacity: 0.2; }
`;

export const FixedTypingIndicator = () => {
  const [isBotSpeaking, setIsBotSpeaking] = useState(false);
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);

  // Bot speaking
  useRTVIClientEvent(
    RTVIEvent.BotStartedSpeaking,
    useCallback(() => { setIsBotSpeaking(true); }, [])
  );
  useRTVIClientEvent(
    RTVIEvent.BotStoppedSpeaking,
    useCallback(() => { setIsBotSpeaking(false); }, [])
  );

  // User speaking
  useRTVIClientEvent(
    RTVIEvent.UserStartedSpeaking,
    useCallback(() => { setIsUserSpeaking(true); }, [])
  );
  useRTVIClientEvent(
    RTVIEvent.UserStoppedSpeaking,
    useCallback(() => {
      setTimeout(() => {
        setIsUserSpeaking(false);
      }, 300);
    }, [])
  );

  const speakingText = isUserSpeaking ? "You" : "Assistant";
  const bgColor = isUserSpeaking ? '#31465F' : '#FFA827';

  return (

    <Paper
      elevation={3}
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: 30,
        padding: '5px 12px',
        backgroundColor: bgColor,
        color: 'white',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
        minWidth: 'auto',
        width: 'fit-content',
        opacity: !isBotSpeaking && !isUserSpeaking ? '0' : '100'
      }}
    >
      <Typography variant="caption" sx={{ fontWeight: 500, fontSize: '0.75rem' }}>
        {speakingText}
      </Typography>
      <Box sx={{ display: isBotSpeaking || isUserSpeaking ? 'flex' : 'none', gap: 0.5, ml: 0.8 }}>
        {[0, 1, 2].map((i) => (
          <Box
            key={i}
            sx={{
              width: '4px',
              height: '4px',
              borderRadius: '50%',
              backgroundColor: 'white',
              animation: `${blink} 1.4s infinite`,
              animationFillMode: 'both',
              animationDelay: `${i * 0.2}s`
            }}
          />
        ))}
      </Box>
    </Paper>

  );
}; 