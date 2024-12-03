import { Box, Button, Card, Center, Code, Flex, Input, Spinner, Table, Text, VisuallyHidden } from "@chakra-ui/react";
import { useEffect, useRef, useState } from "react";
import Auth, { AuthSession } from "./components/auth";
import { FaDoorOpen, FaDownload, FaUpload } from "react-icons/fa";
import { apiClient } from "./functions/requests";
import {
	ProgressCircleRing,
	ProgressCircleRoot,
} from "@/components/ui/progress-circle"
import { toaster } from '@/components/ui/toaster'

export type Status = {
	status: string,
	progress: number
}

export default function App() {
	const inputRef = useRef<HTMLInputElement>(null)
	const [authSession, setAuthSession] = useState<AuthSession>()
	const [status, setStatus] = useState<Record<string, Status>>()

	const handleInputSubmit: React.ChangeEventHandler<HTMLInputElement> = async (e) => {
		if (!e.target.files) return
		for (const file of e.target.files) {
			const toast = toaster.create({
				type: 'loading',
				title: `Uploading ${file.name}`,
				description: `Please be patient, your video is ${file.size} bytes big`,
				action: {
					label: 'Close',
					onClick: () => undefined
				}
			})
			const formdata = new FormData()
			formdata.append('video', file)
			apiClient.post('/api/jobs', formdata, {
				headers: {
					'Content-Type': 'multipart/form-data',
					'Authorization': authSession.token
				}
			}).then(() => toaster.remove(toast))
		}
	}

	useEffect(() => {
		if (!authSession) return
		const interval = setInterval(() => {
			apiClient.get<Record<string, Status>>('/api/status', {
				headers: {
					Authorization: authSession.token
				}
			})
				.then(r => setStatus(r.data))
				.catch(e => console.log(e))
		}, 5000)

		return () => clearInterval(interval)
	}, [authSession])

	useEffect(() => {
		console.log(status)
	}, [status])
	if (!authSession) return (
		<Auth onAuth={(as) => setAuthSession(as)} />
	)
	return (
		<Flex w='100vw' h='100vh' maxW='100vw' maxH='100vh' flexDir='column'>
			<Card.Root flexDir='row' borderRadius={0} alignItems='center' padding='3' gap={3}>
				<Code fontSize='xl'>VIGIU</Code>
				<Box flex={1} />
				<Button onClick={() => setAuthSession(undefined)}>
					<FaDoorOpen size={14} />
					<Text fontSize={17}>Log out of {authSession.email}</Text>
				</Button>
			</Card.Root>
			<Center flex={1} w='100%' flexDir='column' gap={3} padding={3} minH={0}>
				<Card.Root minW='600px' flex={1} minH={0}>
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
										<Table.ColumnHeader textAlign='center'>Status</Table.ColumnHeader>
										<Table.ColumnHeader textAlign='end'>Progress</Table.ColumnHeader>
									</Table.Row>
								</Table.Header>
								<Table.Body>
									{Object.entries(status).map(([key, value]) => (
										<Table.Row key={key}>
											<Table.Cell>{key}</Table.Cell>
											<Table.Cell textAlign='center'>{value.status}</Table.Cell>
											<Table.Cell textAlign='end'>
												{value.progress == 100 ? (
													<Button><FaDownload />Download Results</Button>
												) : (
													<ProgressCircleRoot value={value.progress} size='xs'>
														<ProgressCircleRing cap='round' />
													</ProgressCircleRoot>
												)}
											</Table.Cell>
										</Table.Row>
									))}
								</Table.Body>
							</Table.Root>
						)}
					</Card.Body>
				</Card.Root>
				<VisuallyHidden>
					<Input multiple type='file' accept='video/*' ref={inputRef} onChange={handleInputSubmit} />
				</VisuallyHidden>
				<Button minW='600px' onClick={() => inputRef.current?.click()}>
					<FaUpload />
					<Text fontSize={17}>Upload New Video</Text>
				</Button>
			</Center>
		</Flex>
	)
}
