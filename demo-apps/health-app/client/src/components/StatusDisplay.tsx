import { useRTVIClientTransportState } from '@pipecat-ai/client-react';
import { Chip, useTheme } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import SyncIcon from '@mui/icons-material/Sync';

export function StatusDisplay() {
  const transportState = useRTVIClientTransportState();
  const theme = useTheme();

  // Determine color and icon based on state
  let color = theme.palette.grey[500];
  let icon = <SyncIcon fontSize="small" />;
  let label = transportState;

  if (transportState === 'connected') {
    color = theme.palette.success.main;
    icon = <CheckCircleIcon fontSize="small" />;
  } else if (transportState === 'disconnected') {
    color = theme.palette.error.main;
    icon = <ErrorIcon fontSize="small" />;
  } else if (transportState === 'connecting') {
    color = theme.palette.warning.main;
  }

  return (
    <Chip
      icon={icon}
      label={label}
      size="small"
      sx={{
        color: 'white',
        bgcolor: color,
        mr: 2,
        textTransform: 'capitalize',
        '& .MuiChip-icon': {
          color: 'white'
        }
      }}
    />
  );
}
