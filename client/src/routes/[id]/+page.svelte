<script>
	import { PUBLIC_API_URL } from '$env/static/public';
	import { onMount } from 'svelte';

	const { data } = $props();
	const id = data.id;

	let files = $state([]);
	let binaries = $state([]);
	let selectedBinary = $state('');
	let commandArgs = $state('');
	let executing = $state(false);
	let output = $state(null);
	let error = $state(null);
	let loading = $state(true);

	onMount(async () => {
		await Promise.all([loadFiles(), loadBinaries()]);
		loading = false;
	});

	async function loadFiles() {
		try {
			const response = await fetch(`${PUBLIC_API_URL}/list/${id}`);
			if (!response.ok) {
				throw new Error('Failed to load files');
			}
			const result = await response.json();
			files = result.files;
		} catch (err) {
			error = err.message;
		}
	}

	async function loadBinaries() {
		try {
			const response = await fetch(`${PUBLIC_API_URL}/binaries`);
			if (!response.ok) {
				throw new Error('Failed to load binaries');
			}
			const result = await response.json();
			binaries = result.binaries;
			if (binaries.length > 0) {
				selectedBinary = binaries[0];
			}
		} catch (err) {
			error = err.message;
		}
	}

	async function executeCommand() {
		if (!selectedBinary) {
			error = 'Please select a binary';
			return;
		}

		executing = true;
		error = null;
		output = null;

		try {
			const args = commandArgs.trim().split(/\s+/).filter(a => a.length > 0);

			const response = await fetch(`${PUBLIC_API_URL}/execute`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					unique_id: id,
					binary: selectedBinary,
					args: args
				})
			});

			if (!response.ok) {
				const data = await response.json();
				throw new Error(data.detail || 'Execution failed');
			}

			output = await response.json();
			await loadFiles(); // Refresh file list
		} catch (err) {
			error = err.message;
		} finally {
			executing = false;
		}
	}

	async function downloadFile(filename) {
		try {
			const response = await fetch(`${PUBLIC_API_URL}/download/${id}/${filename}`);

			if (!response.ok) {
				const data = await response.json();
				throw new Error(data.detail || 'Download failed');
			}

			const result = await response.json();

			// Create a blob from the content
			const blob = new Blob([result.content], { type: 'text/plain' });

			// Create a download link and trigger it
			const url = window.URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = result.filename; // Use the filename from the response
			document.body.appendChild(a);
			a.click();
			window.URL.revokeObjectURL(url);
			document.body.removeChild(a);
		} catch (err) {
			error = err.message;
		}
	}

	async function removeWorkspace() {
		if (!confirm('Please confirm that you want to permananetly and irreversibly remove all data in this workspace. This cannot be undone.')) {
			return;
		}

		try {
			const response = await fetch(`${PUBLIC_API_URL}/cleanup/${id}`, {
				method: 'DELETE'
			});

			if (!response.ok) {
				const data = await response.json();
				throw new Error(data.detail || 'Cleanup failed');
			}

			// Redirect to home page after successful cleanup
			window.location.href = '/';
		} catch (err) {
			error = err.message;
		}
	}
</script>

<div class="container">
	<header class="header">
		<div style="display: flex; justify-content: space-between; align-items: baseline;">
			<div>
				<h1 style="color: var(--blue)">
					<span style="font-family: Kanit; font-variant: small-caps;" class="italic">Batchalign</span> WebCLAN
				</h1>
			</div>
		</div>
	</header>

	{#if loading}
		<p>Loading workspace...</p>
	{:else}
		<div class="section">
			<div class="title-bar">
				<h2 class="section-title">Files</h2>
				<div class="progress-bar"></div>
			</div>

			{#if files.length > 0}
				<table class="file-table">
					<thead>
						<tr>
							<th>Name</th>
							<th>Type</th>
							<th>Size</th>
							<th style="width: 25px">Action</th>
						</tr>
					</thead>
					<tbody>
						{#each files as file}
							<tr>
								<td>{file.name}</td>
								<td>{file.type}</td>
								<td>{file.size ? `${file.size} bytes` : '-'}</td>
								<td style="width: 25px">
									{#if file.type === 'file'}
										<button class="download-btn" on:click={() => downloadFile(file.name)}>
											Download
										</button>
									{/if}
								</td>
							</tr>
						{/each}
						<tr class="remove-workspace-row">
							<td colspan="3">Remove Workspace</td>
							<td style="width: 25px">
								<button class="remove-btn" on:click={removeWorkspace}>
									Remove
								</button>
							</td>
						</tr>
					</tbody>
				</table>
			{:else}
				<p class="instructions">No files in workspace.</p>
			{/if}
		</div>

		<div class="section">
			<div class="title-bar">
				<h2 class="section-title">Execute Command</h2>
				<div class="progress-bar {error ? 'error' : ''}"></div>
			</div>

			{#if error}
				<p class="error-message">
					Execution encountered a failure. <span class="error-detail">{error}</span>
				</p>
			{/if}

			<p class="instructions">
				Select a CLAN binary and provide arguments to execute commands in your workspace.
			</p>

			<div class="command-form">
				<div class="form-row">
					<label for="binary">Binary:</label>
					<select id="binary" bind:value={selectedBinary} disabled={executing}>
						{#each binaries as binary}
							<option value={binary}>{binary}</option>
						{/each}
					</select>
				</div>

				<div class="form-row">
					<label for="args">Arguments:</label>
					<input
						type="text"
						id="args"
						bind:value={commandArgs}
						placeholder="Enter the arguments and flags of your command here, such as the input file name."
						disabled={executing}
						on:keydown={(e) => e.key === 'Enter' && executeCommand()}
					/>
				</div>

				<div class="submit-container">
					<button class="submit-btn" on:click={executeCommand} disabled={executing || !selectedBinary}>
						{executing ? 'Executing...' : 'Execute'}
					</button>
				</div>
			</div>

			{#if output}
				<div class="output-section">
					<h3>Output</h3>
					<!-- <div class="output-details"> -->
					<!-- 	<p><strong>Return Code:</strong> {output.returncode}</p> -->
					<!-- </div> -->

					{#if output.stdout}
						<div class="output-box">
							<!-- <h4>stdout</h4> -->
							<pre>{output.stdout}</pre>
						</div>
					{/if}

					{#if output.stderr}
						<div class="output-box error">
							<!-- <h4>stderr</h4> -->
							<pre>{output.stderr}</pre>
						</div>
					{/if}
				</div>
			{/if}
		</div>
	{/if}

	<footer class="footer">The Talkbank System</footer>
</div>

<style>
	.container {
		max-width: 1200px;
		margin: 0 auto;
        margin-top: 50px;
		padding: 20px 80px;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;
	}

	.section {
		margin-bottom: 60px;
	}

	.title-bar {
		display: flex;
		align-items: center;
		gap: 20px;
		margin-bottom: 20px;
	}

	.section-title {
		font-size: 20px;
		font-weight: 700;
		margin: 0;
		color: var(--black);
		white-space: nowrap;
	}

	.progress-bar {
		height: 8px;
		background-color: var(--teal);
		border-radius: 0;
		flex: 1;
	}

	.progress-bar.error {
		background-color: var(--red);
	}

	.instructions {
		font-size: 16px;
		line-height: 1.6;
		margin-bottom: 20px;
		color: var(--black);
	}

	.error-message {
		font-size: 16px;
		margin-bottom: 8px;
		color: var(--black);
	}

	.error-detail {
		color: var(--red);
	}

	.file-table {
		width: 100%;
		border-collapse: collapse;
		margin-bottom: 20px;
		border: 1px solid #ccc;
	}

	.file-table thead {
		background-color: #f5f5f5;
	}

	.file-table th {
		text-align: left;
		padding: 4px 16px;
		font-weight: 700;
		border-bottom: 1px solid #ccc;
		color: var(--black);
	}

	.file-table td {
		padding: 8px 16px;
		border-bottom: 1px solid #e0e0e0;
		color: var(--black);
	}

	.file-table tbody tr:last-child td {
		border-bottom: none;
	}

	.remove-workspace-row {
		background-color: #f5f5f5;
	}

	.remove-workspace-row td {
		font-weight: 600;
		color: #666;
	}

	.remove-btn {
		background-color: var(--red);
		color: white;
		border: none;
		padding: 2px 15px;
		font-size: 14px;
		font-weight: 400;
		cursor: pointer;
	}

	.remove-btn:hover {
		opacity: 0.9;
	}

	.download-btn {
		background-color: var(--teal);
		color: white;
		border: none;
		padding: 2px 15px;
		font-size: 14px;
		font-weight: 400;
		cursor: pointer;
	}

	.download-btn:hover {
		opacity: 0.9;
	}

	.command-form {
		background-color: #f9f9f9;
		padding: 20px;
		border: 1px solid #ccc;
		margin-bottom: 20px;
	}

	.form-row {
		margin-bottom: 15px;
	}

	.form-row label {
		display: block;
		font-weight: 600;
		margin-bottom: 5px;
		color: var(--black);
	}

	.form-row select,
	.form-row input {
		width: 100%;
		padding: 8px;
		border: 1px solid #ccc;
		background-color: white;
		font-size: 14px;
	}

	.submit-container {
		margin-top: 20px;
		text-align: right;
	}

	.submit-btn {
		background-color: var(--teal);
		color: white;
		border: none;
		padding: 2px 15px;
		font-size: 14px;
		font-weight: 400;
		cursor: pointer;
	}

	.submit-btn:hover:not(:disabled) {
		opacity: 0.9;
	}

	.submit-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.output-section {
		margin-top: 30px;
		padding: 20px;
		background-color: #f5f5f5;
		border: 1px solid #ccc;
	}

	.output-section h3 {
		margin-top: 0;
		color: var(--black);
	}

	.output-details {
		margin-bottom: 15px;
	}

	.output-box {
		margin-bottom: 20px;
	}

	.output-box h4 {
		margin: 0 0 10px 0;
		color: var(--black);
	}

	.output-box pre {
		background-color: white;
		border: 1px solid #ccc;
		padding: 15px;
		overflow-x: auto;
		margin: 0;
		color: var(--black);
		font-family: monospace;
		white-space: pre-wrap;
		word-wrap: break-word;
	}

	.output-box.error pre {
		border-color: var(--red);
		background-color: #fff5f5;
	}

	.footer {
		text-align: center;
		font-size: 18px;
		color: #ccc;
		margin-top: 60px;
        margin-bottom: 50px;
	}
</style>
