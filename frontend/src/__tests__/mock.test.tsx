import React from "react";
import { render, screen } from "@testing-library/react";

describe("Mock Test Suite", () => {
  it("renders a dummy heading and checks content exists", () => {
    render(<h1>AI LMS Platform</h1>);
    expect(screen.getByText("AI LMS Platform")).toBeInTheDocument();
  });
});
