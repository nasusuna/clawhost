"use client";

import { Component, type ReactNode } from "react";
import Link from "next/link";

type Props = { children: ReactNode };

type State = { hasError: boolean; error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <main className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background px-6 text-foreground">
          <h1 className="text-2xl font-bold">Something went wrong</h1>
          <p className="max-w-md text-center text-muted-foreground">
            An unexpected error occurred. Please try again or return to the home page.
          </p>
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => this.setState({ hasError: false, error: null })}
              className="rounded-lg border border-border bg-secondary px-4 py-2 text-sm font-medium hover:bg-accent"
            >
              Try again
            </button>
            <Link
              href="/"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90"
            >
              Go home
            </Link>
          </div>
        </main>
      );
    }
    return this.props.children;
  }
}
