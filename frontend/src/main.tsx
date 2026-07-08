import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";
import "./index.css";
import { shouldRetryRead } from "./lib/errors";
import { router } from "./routes";

const queryClient = new QueryClient({
  defaultOptions: {
    // Mutations never auto-retry (plan §6.6). Queries retry only on
    // transient (non-4xx) failures — a 404/429 is terminal, not transient,
    // and retrying it just delays the UI from showing the real state.
    queries: { retry: shouldRetryRead },
    mutations: { retry: false },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
