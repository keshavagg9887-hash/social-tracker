import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  style,
  ...props
}) => {
  return (
    <button
      style={{
        padding: '8px 16px',
        borderRadius: '6px',
        cursor: 'pointer',
        ...style,
      }}
      {...props}
    >
      {children}
    </button>
  );
};
