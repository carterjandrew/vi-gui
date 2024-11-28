import { Box, Button, Card, Center, Code, Flex, Spinner, Table, Text } from "@chakra-ui/react";
import { useEffect, useState } from "react";
import Auth, { AuthSession } from "./components/auth";
import { FaDoorOpen, FaUpload, FaUser } from "react-icons/fa";
import { apiClient } from "./functions/requests";

export type Status = {
	status: string,
	progress: number
}

export default function App() {
	const [authSession, setAuthSession] = useState<AuthSession>({
		"email": "temp",
		"token": "b2c0969f61523776fb6dbe5c3ae845e03d67b8c94284058c2bf17c39fc5dee80"
	})
	const [status, setStatus] = useState<Status[]>()

	useEffect(() => {
		apiClient.get<Status[]>('/api/status').then(r => setStatus(r.data))
	}, [authSession])

	useEffect(() => {
		console.log(status)
	}, [status])
	if (!authSession) return (
		<Auth onAuth={(as) => setAuthSession(as)} />
	)
	return (
		<Flex w='100vw' h='100vh' flexDir='column'>
			<Card.Root flexDir='row' borderRadius={0} alignItems='center' padding='3' gap={3}>
				<Code fontSize='xl'>VIGIU</Code>
				<Box flex={1} />
				<Button onClick={() => setAuthSession(undefined)}>
					<FaDoorOpen size={14} />
					<Text fontSize={17}>Log out of {authSession.email}</Text>
				</Button>
			</Card.Root>
			<Center flex={1} w='100%' h='100%' flexDir='column' gap={3} padding={3}>
				<Card.Root minW='600px' flex={1}>
					<Card.Header fontSize='xl'>Jobs</Card.Header>
					<Card.Body maxH='100%' overflowY='scroll'>
						{!status ? (
							<Center flexDir='column' gap={3} w='full'>
								<Spinner />
								<Text>Loading Jobs...</Text>
							</Center>
						) : Object.keys(status).length == 0 ? (
							<Center flexDir='column' gap={3} w='full'>
								<Text>No Jobs Yet...</Text>
							</Center>
						) : (
							<Table.Root>
								<Table.Header>
									<Table.Row>
										<Table.ColumnHeader>Job Name</Table.ColumnHeader>
										<Table.ColumnHeader>Status</Table.ColumnHeader>
										<Table.ColumnHeader>Dowload Link</Table.ColumnHeader>
									</Table.Row>
								</Table.Header>
								<Table.Body>
								</Table.Body>
							</Table.Root>
						)}
					</Card.Body>
				</Card.Root>
				<Button minW='600px'>
				<FaUpload />
				<Text fontSize={17}>Upload New Video</Text>
				</Button>
			</Center>
		</Flex>
	)
}
