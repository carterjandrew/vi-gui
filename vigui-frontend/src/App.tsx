import { createBrowserRouter, RouterProvider } from "react-router"
import RootLayout from "./layouts/rootLayout"

const router = createBrowserRouter([
	{
		path: '/',
		Component: RootLayout
	}
])

function App() {
	return (
		<RouterProvider router={router} />
	)
}

export default App
