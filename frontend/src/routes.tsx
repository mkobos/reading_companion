import { createBrowserRouter } from "react-router-dom";
import { NotFoundPage } from "./workspace/NotFoundPage";
import { RootRedirect } from "./workspace/RootRedirect";
import { WorkspacePage } from "./workspace/WorkspacePage";

export const router = createBrowserRouter([
  { path: "/", element: <RootRedirect /> },
  { path: "/w/:workspaceId", element: <WorkspacePage /> },
  { path: "*", element: <NotFoundPage /> },
]);
