import styled from '@emotion/styled';

// Modern chat input container
export const InputContainer = styled.div`
  padding: 15px;
  display: flex;
  gap: 12px;
  background: #FFF1E0; // Light orange background
  border-top: 1px solid #FFDFBF;
  align-items: center;
  position: relative;
`;

// Decorative element
export const InputDecorations = styled.div`
  position: absolute;
  top: -15px;
  left: 0;
  right: 0;
  height: 15px;
  background: linear-gradient(to bottom, transparent, rgba(255, 223, 191, 0.5));
`;

// Text field styling for Material UI
export const textFieldStyles = {
  '& .MuiOutlinedInput-root': {
    borderRadius: '20px',
    backgroundColor: '#FFFFFF',
    color: '#663C00',
    fontFamily: "'Arial', sans-serif",
    '& fieldset': {
      borderColor: '#FFCC99',
      borderWidth: '1px'
    },
    '&:hover fieldset': {
      borderColor: '#FFBB66'
    },
    '&.Mui-focused fieldset': {
      borderColor: '#FF9933'
    }
  },
  '& .MuiOutlinedInput-input': {
    padding: '12px 20px',
    fontSize: '15px',
    '&::placeholder': {
      color: '#BF8040',
      opacity: 0.7
    }
  }
};

// Button styling for Material UI
export const sendButtonStyles = {
  minWidth: 55,
  height: 55,
  borderRadius: '50%',
  padding: 0,
  background: '#FF9933',
  color: '#FFFFFF',
  boxShadow: '0 3px 5px rgba(255, 153, 51, 0.3)',
  transition: 'all 0.2s ease',
  '&:hover': {
    background: '#FF8000',
    transform: 'scale(1.05)'
  },
  '&:active': {
    transform: 'scale(0.95)'
  },
  '&.Mui-disabled': {
    backgroundColor: '#FFE0CC',
    color: '#CCAA88'
  },
  '&::after': {
    content: '"➤"',
    fontSize: '20px'
  }
}; 