import React, { forwardRef } from "react";
import { VariantProps, cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

// Form Components
export const FormGroup = ({ className, ...props }) => (
  <div className={cn("space-y-2", className)} {...props} />
);

export const FormLabel = ({ className, ...props }) => (
  <label
    className={cn("text-sm font-medium text-foreground", className)}
    {...props}
  />
);

export const FormDescription = ({ className, ...props }) => (
  <p className={cn("text-sm text-muted-foreground", className)} {...props} />
);

// Layout Components
export const Grid = ({ className, children, cols = 1, ...props }) => (
  <div
    className={cn(
      "grid",
      {
        "grid-cols-1": cols === 1,
        "grid-cols-2": cols === 2,
        "grid-cols-3": cols === 3,
        "grid-cols-4": cols === 4,
      },
      "gap-4",
      className,
    )}
    {...props}
  >
    {children}
  </div>
);

export const Flex = ({ className, ...props }) => (
  <div className={cn("flex", className)} {...props} />
);

// Status Indicator
export const StatusIndicator = ({ status, className, ...props }) => (
  <span
    className={cn(
      "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
      {
        "bg-green-100 text-green-800": status === "success",
        "bg-red-100 text-red-800": status === "error",
        "bg-yellow-100 text-yellow-800": status === "warning",
        "bg-blue-100 text-blue-800": status === "info",
      },
      className,
    )}
    {...props}
  />
);

// Loading Spinner
export const Spinner = ({ className, size = "md", ...props }) => (
  <div
    className={cn(
      "animate-spin rounded-full border-2 border-current border-t-transparent",
      {
        "h-4 w-4": size === "sm",
        "h-6 w-6": size === "md",
        "h-8 w-8": size === "lg",
      },
      className,
    )}
    {...props}
  />
);

// Alert Component
const alertVariants = cva("relative w-full rounded-lg border p-4", {
  variants: {
    variant: {
      default: "bg-background text-foreground",
      destructive: "border-red-500 text-red-500 bg-red-50 dark:bg-red-900/10",
    },
  },
  defaultVariants: {
    variant: "default",
  },
});

export const Alert = ({ className, variant, ...props }) => (
  <div className={cn(alertVariants({ variant }), className)} {...props} />
);

export const AlertTitle = ({ className, ...props }) => (
  <h5
    className={cn("mb-1 font-medium leading-none tracking-tight", className)}
    {...props}
  />
);

export const AlertDescription = ({ className, ...props }) => (
  <div className={cn("text-sm opacity-90", className)} {...props} />
);

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?:
    | "default"
    | "destructive"
    | "outline"
    | "secondary"
    | "ghost"
    | "link";
  size?: "default" | "sm" | "lg" | "icon";
}

// Button Component
const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-red-500 text-white hover:bg-red-600",
        outline:
          "border border-input hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "underline-offset-4 hover:underline text-primary",
      },
      size: {
        default: "h-10 py-2 px-4",
        sm: "h-9 px-3",
        lg: "h-11 px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  ),
);
Button.displayName = "Button";

// Card Components
export const Card = ({ className, ...props }) => (
  <div
    className={cn(
      "rounded-lg border bg-card text-card-foreground shadow-sm",
      className,
    )}
    {...props}
  />
);

export const CardHeader = ({ className, ...props }) => (
  <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />
);

export const CardTitle = ({ className, ...props }) => (
  <h3
    className={cn(
      "text-lg font-semibold leading-none tracking-tight",
      className,
    )}
    {...props}
  />
);

export const CardContent = ({ className, ...props }) => (
  <div className={cn("p-6 pt-0", className)} {...props} />
);

// Tabs Components
export const Tabs = ({ className, ...props }) => (
  <div className={cn("w-full", className)} {...props} />
);

export const TabsList = ({ className, ...props }) => (
  <div
    className={cn(
      "inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground",
      className,
    )}
    {...props}
  />
);

export const TabsTrigger = ({ className, selected, ...props }) => (
  <button
    className={cn(
      "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
      selected
        ? "bg-background text-foreground shadow-sm"
        : "hover:bg-gray-100",
      className,
    )}
    {...props}
  />
);

export const TabsContent = ({ className, ...props }) => (
  <div
    className={cn(
      "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
      className,
    )}
    {...props}
  />
);

// Input Component
export const Input = forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement> & { className?: string }
>(({ className, type = "text", ...props }, ref) => (
  <input
    type={type}
    className={cn(
      "flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
      className,
    )}
    ref={ref}
    {...props}
  />
));
Input.displayName = "Input";

export default {
  Alert,
  AlertTitle,
  AlertDescription,
  Button,
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
  Input,
};
