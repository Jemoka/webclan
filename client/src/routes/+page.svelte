<script>
	import { PUBLIC_API_URL } from '$env/static/public';

	let file = null;
	let uploading = false;
	let result = null;
	let error = null;

	function handleFileChange(event) {
		file = event.target.files[0];
		result = null;
		error = null;
	}

	async function handleSubmit(event) {
		event.preventDefault();

		if (!file) {
			error = 'Please select a file';
			return;
		}

		uploading = true;
		error = null;
		result = null;

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

			result = await response.json();
		} catch (err) {
			error = err.message;
		} finally {
			uploading = false;
		}
	}
</script>

<div style="min-width: 500px; padding: 8px 0;">
    <h2>Upload</h2>
	<form on:submit={handleSubmit}>
		<div class="form-group">
			<input
				type="file"
				id="file"
				accept=".cha"
				on:change={handleFileChange}
				disabled={uploading}
			/>
		</div>

		<button type="submit" disabled={!file || uploading}>
			{uploading ? 'Uploading...' : 'Upload'}
		</button>
	</form>

	{#if error}
		<div class="error">
			<strong>Error:</strong> {error}
		</div>
	{/if}

	{#if result}
		<div class="result">
			<h2>Upload Successful!</h2>
			<dl>
				<dt>Unique ID:</dt>
				<dd>{result.unique_id}</dd>

				<dt>Filename:</dt>
				<dd>{result.filename}</dd>

				<dt>Size:</dt>
				<dd>{result.size} bytes</dd>

				<dt>Path:</dt>
				<dd>{result.path}</dd>
			</dl>
		</div>
	{/if}
</div>

