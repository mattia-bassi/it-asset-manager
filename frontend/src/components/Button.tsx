import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'destructive';
  icon?: string;
  children?: React.ReactNode;
  fullWidth?: boolean;
  iconOnly?: boolean; // NUOVO: mostra solo icona (per tabelle)
}

const Button: React.FC<ButtonProps> = ({ 
  variant = 'primary', 
  icon, 
  children, 
  fullWidth = false,
  iconOnly = false, // NUOVO: default false
  className = '',
  title, // tooltip
  ...props 
}) => {
  const baseClasses = iconOnly 
    ? 'px-2 py-2 text-base' // Bottone compatto per icone
    : 'px-4 py-2 text-sm';   // Bottone normale

  return (
    <button
      className={`${baseClasses} rounded-lg font-semibold transition-colors whitespace-nowrap ${
        fullWidth ? 'w-full' : ''
      } ${
        variant === 'primary' 
          ? 'bg-asset-manager-yellow hover:bg-yellow-300 text-asset-manager-gray'
          : variant === 'secondary'
          ? 'bg-asset-manager-gray hover:bg-gray-600 text-white'
          : 'bg-red-600 hover:bg-red-700 text-white'
      } disabled:opacity-50 disabled:cursor-not-allowed ${className}`}
      title={title} // Tooltip importante per iconOnly
      {...props}
    >
      {iconOnly ? (
        // Solo icona (per tabelle)
        icon
      ) : (
        // Icona + Testo (per modal/header)
        <>
          {icon && <span className="mr-2">{icon}</span>}
          {children}
        </>
      )}
    </button>
  );
};

export default Button;
