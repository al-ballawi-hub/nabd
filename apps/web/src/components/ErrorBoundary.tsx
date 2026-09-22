import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = { children: ReactNode };
type State = { hasError: boolean };

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Uncaught render error:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center p-6">
          <div className="w-full max-w-md rounded-3xl border border-white/50 bg-white/85 p-8 text-center shadow-2xl shadow-teal-900/20 backdrop-blur-md">
            <h1 className="text-2xl font-bold text-slate-800">
              Something went wrong
            </h1>
            <p className="mt-2 text-slate-600">
              An unexpected error occurred. Please reload the page to continue.
            </p>
            <button
              className="mt-5 rounded-2xl bg-gradient-to-br from-teal-600 to-emerald-600 px-6 py-2.5 font-semibold text-white shadow-lg transition hover:-translate-y-0.5 active:scale-95"
              onClick={() => window.location.reload()}
            >
              Reload
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
