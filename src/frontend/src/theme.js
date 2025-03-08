import { createTheme } from '@mui/material';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#E57373', // warm red
      dark: '#D32F2F',
    },
    secondary: {
      main: '#FFB74D', // warm orange
    },
    background: {
      default: '#FFF3E0', // warm light orange
      paper: '#FFFFFF',
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          background: 'linear-gradient(135deg, #FF8A65 0%, #E57373 100%)',
        },
      },
    },
  },
}); 