import { Button, Flex } from "@chakra-ui/react";
import { useEffect, useState } from "react";

export default function RootLayout() {
	const [status, setStatus] = useState()
	useEffect(() => {
		async function fetchStatus() {
			const response = await fetch(`http://${import.meta.env.VITE_API_ADDRESS}/api/status`)
			console.log(await response.text())
		}
		fetchStatus()
	}, [])
	return (
		<Flex w='100%' h='100%' flexDir='column'>
			<Flex w='100%'>
			</Flex>
		</Flex>
	)
}
