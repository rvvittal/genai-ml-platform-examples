import { ThemeProvider as MUIThemeProvider, createTheme } from '@mui/material/styles';
import { PropsWithChildren } from 'react';

const theme = createTheme({
  typography: {
    fontFamily: '"Amazon Ember", sans-serif',
  },
});

export function ThemeProvider({ children }: PropsWithChildren) {
  return <MUIThemeProvider theme={theme}>{children}</MUIThemeProvider>;
} 