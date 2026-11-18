import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HomePage } from "../pages/HomePage";

function renderHomePage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <HomePage />
      </BrowserRouter>
    </QueryClientProvider>,
  );
}

describe("HomePage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the product foundation without pretending query execution exists", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ status: "ok" }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    renderHomePage();

    expect(
      screen.getByRole("heading", { name: /your data\. your questions\./i }),
    ).toBeInTheDocument();
    expect(await screen.findByText("API online")).toBeInTheDocument();
    expect(screen.getByText(/query workspace is not available yet/i)).toBeInTheDocument();
  });
});
