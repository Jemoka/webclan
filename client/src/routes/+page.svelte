<script>
	import { PUBLIC_API_URL } from '$env/static/public';
    import { goto } from '$app/navigation';

	let file = null;
	let uploading = false;
	let error = null;
	let dragActive = false;

	function handleFileSelect(event) {
		const selectedFiles = Array.from(event.target.files || []);
		if (selectedFiles.length > 0) {
			addFile(selectedFiles[0]);
		}
	}

	function handleDrop(event) {
		event.preventDefault();
		dragActive = false;
		const droppedFiles = Array.from(event.dataTransfer.files);
		const chaFiles = droppedFiles.filter(f => f.name.endsWith('.cha'));
		if (chaFiles.length > 0) {
			addFile(chaFiles[0]);
		}
	}

	function handleDragOver(event) {
		event.preventDefault();
		dragActive = true;
	}

	function handleDragLeave(event) {
		event.preventDefault();
		dragActive = false;
	}

	function addFile(newFile) {
		if (newFile.name.endsWith('.cha')) {
			file = newFile;
			error = null;
		}
	}

	function removeFile() {
		file = null;
	}

	function triggerFileInput() {
		document.getElementById('fileInput').click();
	}

	async function handleSubmit() {
		if (!file) {
			error = 'Please select a file';
			return;
		}

		uploading = true;
		error = null;

		try {
			const formData = new FormData();
			formData.append('file', file);

			const response = await fetch(`${PUBLIC_API_URL}/upload`, {
				method: 'POST',
				body: formData
			});

			if (!response.ok) {
				const data = await response.json();
				throw new Error(data.detail || 'Upload failed');
			}

			const result = await response.json();
            goto(`/${result.unique_id}`);
			// console.log('Upload result:', result);
			// Handle success
		} catch (err) {
			error = err.message;
		} finally {
			uploading = false;
		}
	}
</script>

<div class="container">
	<header class="header">
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <div><h1 style="color: var(--blue)"><span style="font-family: Kanit; font-variant: small-caps;" class="italic">Batchalign</span> WebCLAN</h1></div>
        </div>
	</header>

	<div class="upload-section">
		<div class="title-bar">
			<h2 class="section-title">Upload</h2>
			<div class="progress-bar {error ? 'error' : ''}"></div>
		</div>

		{#if error}
			<p class="error-message">Upload encountered a failure. <span class="error-detail">{error}</span></p>
		{/if}

		<p class="instructions">
			To begin using WebCLAN, please upload the CHAT files you wish to work with.
			{#if !error}
				<br>We will generate a new working directory for you to enter CLAN commands in the next screen.
			{/if}
		</p>

		{#if file}
			<table class="file-table">
				<thead>
					<tr>
						<th>File Name</th>
						<th  style="width: 25px">Action</th>
					</tr>
				</thead>
				<tbody>
					<tr>
						<td>{file.name}</td>
						<td style="width: 25px">
							<button class="remove-btn" style="float: left" on:click={removeFile}>Remove</button>
						</td>
					</tr>
				</tbody>
			</table>
		{/if}

		<input
			type="file"
			id="fileInput"
			accept=".cha"
			on:change={handleFileSelect}
			style="display: none;"
		/>

        {#if !file}
		<div
			class="dropzone {dragActive ? 'drag-active' : ''}"
			on:drop={handleDrop}
			on:dragover={handleDragOver}
			on:dragleave={handleDragLeave}
			on:click={triggerFileInput}
			role="button"
			tabindex="0"
		>
			<p class="dropzone-text">
				Tap here to choose {file ? 'a different ' : 'a '}file<span class="light">, or<br>drop a .cha file in this box.</span>
			</p>
		</div>
        {/if}

		<div class="submit-container">
			<button class="submit-btn" on:click={handleSubmit} disabled={uploading || !file}>
				{uploading ? 'Uploading...' : 'Submit'}
			</button>
		</div>
	</div>

	<footer class="footer">
		The Talkbank System
	</footer>
</div>

<style>
	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 20px 80px;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 20px;
	}

	.title {
		font-size: 32px;
		font-weight: 700;
		margin: 0;
		color: var(--black);
	}

	.batch {
		font-style: italic;
	}

	.system-name {
		font-size: 18px;
		color: var(--black);
	}

	.upload-section {
		margin-bottom: 100px;
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

	.error-message {
		font-size: 16px;
		margin-bottom: 8px;
		color: var(--black);
	}

	.error-detail {
		color: var(--red);
	}

	.instructions {
		font-size: 16px;
		line-height: 1.6;
		margin-bottom: 30px;
		color: var(--black);
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

	.file-table th:last-child {
		/* text-align: right; */
	}

	.file-table td {
		padding: 8px 16px;
		border-bottom: 1px solid #e0e0e0;
		color: var(--black);
	}

	.file-table td:last-child {
		text-align: right;
	}

	.file-table tbody tr:last-child td {
		border-bottom: none;
	}

	.remove-btn {
		background-color: var(--red);
		color: white;
		border: none;
		padding: 2px 15px;
		/* border-radius: 4px; */
		font-size: 14px;
		font-weight: 400;
		cursor: pointer;
	}

	.remove-btn:hover {
		opacity: 0.9;
	}

	.submit-container {
		margin-top: 20px;
		text-align: center;
	}

	.submit-btn {
		background-color: var(--teal);
		color: white;
		border: none;
		padding: 2px 15px;
		font-size: 14px;
		font-weight: 400;
		cursor: pointer;
        float: right;
	}

	.submit-btn:hover:not(:disabled) {
		opacity: 0.9;
	}

	.submit-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.dropzone {
		border: 2px solid #ccc;
		border-radius: 4px;
		padding: 120px 40px;
		text-align: center;
		cursor: pointer;
		transition: border-color 0.2s;
		background-color: #f9f9f9;
	}

	.dropzone:hover,
	.dropzone.drag-active {
		border-color: var(--teal);
	}

	.dropzone-text {
		font-size: 20px;
		color: var(--blue);
		margin: 0;
	}

	.dropzone-text .light {
		color: #999;
		font-weight: 300;
	}

	.footer {
		text-align: center;
		font-size: 18px;
		color: #ccc;
		margin-top: 60px;
	}
</style>
