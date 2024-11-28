import { Card, Flex, Code, Input, Group, InputAddon, Button, Text } from "@chakra-ui/react";
import { PasswordInput } from "@/components/ui/password-input"
import { FaUser, FaLock, FaCheckCircle } from "react-icons/fa";
import { useState } from "react";
import { apiClient } from "@/functions/requests";

export type AuthSession = {
	email: string,
	token: string
}

const Auth: React.FC<{ onAuth: (fi: AuthSession) => void }> = ({ onAuth }) => {
	const [hideConfirmPassword, setHideConfirmPassword] = useState(true)
	const [loginError, setLoginError] = useState('')
	const [username, setUsername] = useState('')
	const [password, setPassword] = useState('')
	const [confirmPW, setConfirmPW] = useState('')

	async function logIn() {
		if (!username) {
			setLoginError("No username entered")
			return
		}
		if (!password) {
			setLoginError("No password entered")
			return
		}
		const response = await apiClient.post<AuthSession>('/api/login', { email: username, password }).catch(e => setLoginError(e.response.data))
		onAuth(response!.data)
	}
	async function signUp() {
		if (hideConfirmPassword) setHideConfirmPassword(false)
		if (!username) {
			setLoginError("No username entered")
			return
		}
		if (!password) {
			setLoginError("No password entered")
			return
		}
		if (confirmPW != password) {
			setLoginError("Passwords do not match")
			return
		}
		const response = await apiClient.post<AuthSession>('/api/signup', { email: username, password }).catch(e => console.log(e))
		onAuth(response!.data)
	}

	return (
		<Flex
			w='100vw'
			h='100vh'
			gap={5}
			flexDir='column'
			justifyContent='center'
			alignItems='center'
		>
			<Code>VIGUI</Code>
			<Flex
				gap={5}
				alignItems='center'
			>
				<Card.Root>
					<Card.Body gap={2}>
						<Group attached w='100%'>
							<InputAddon><FaUser /></InputAddon>
							<Input
								value={username}
								onChange={e => setUsername(e.target.value)}
								placeholder='johnnyappleseed'
							/>
						</Group>
						<Group attached>
							<InputAddon><FaLock /></InputAddon>
							<PasswordInput
								value={password}
								onChange={e => setPassword(e.target.value)}
								placeholder='StrongPassword65!'
							/>
						</Group>
						{hideConfirmPassword ? (<></>) : (
							<Group attached>
								<InputAddon><FaCheckCircle /></InputAddon>
								<PasswordInput
									value={confirmPW}
									onChange={e => setConfirmPW(e.target.value)}
									placeholder='Confirm Password'
								/>
							</Group>
						)}
						{loginError && (
							<Code as='span' color='red'>{loginError}</Code>
						)}
						<Flex gap={2}>
							<Button
								flex={1}
								type='submit'
								onClick={logIn}
							>Log In</Button>
							<Button
								flex={1}
								type='submit'
								onClick={signUp}
							>Sign Up</Button>
						</Flex>
					</Card.Body>
				</Card.Root>
			</Flex>
		</Flex >
	)
}

export default Auth
