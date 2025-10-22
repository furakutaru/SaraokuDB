import * as React from "react"

interface CustomButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean
}

const CustomButton = React.forwardRef<HTMLButtonElement, CustomButtonProps>(
  ({ className, children, active = false, ...props }, ref) => {
    return (
      <button
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          whiteSpace: 'nowrap',
          borderRadius: '0.375rem',
          fontSize: '0.875rem',
          fontWeight: 500,
          transitionProperty: 'color, background-color, border-color, text-decoration-color, fill, stroke',
          transitionTimingFunction: 'cubic-bezier(0.4, 0, 0.2, 1)',
          transitionDuration: '150ms',
          outline: 'none',
          height: '2.5rem',
          padding: '0 1rem',
          color: 'white',
          backgroundColor: active ? '#ea580c' : '#fb923c',
          border: 'none',
          cursor: 'pointer',
        }}
        onMouseOver={(e) => {
          const target = e.currentTarget as HTMLButtonElement;
          target.style.backgroundColor = active ? '#c2410c' : '#f97316';
        }}
        onMouseOut={(e) => {
          const target = e.currentTarget as HTMLButtonElement;
          target.style.backgroundColor = active ? '#ea580c' : '#fb923c';
        }}
        ref={ref}
        {...props}
      >
        {children}
      </button>
    )
  }
)
CustomButton.displayName = "CustomButton"

export { CustomButton }
