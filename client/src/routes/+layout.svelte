<script>
	import favicon from '$lib/assets/talkbank.ico';

	let { children } = $props();
    import "../app.css";
    import "$lib/styles/typography.css";
</script>

<svelte:head>
    <link rel="icon" href={favicon} />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Geologica:wght@100..900&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Kanit:ital,wght@0,400;1,600&display=swap" rel="stylesheet">
</svelte:head>

<div style="display: flex; align-items: center; justify-content: center; min-height: 100vh;">
    <div style="max-width: 1000px; margin: 0 auto">
        {@render children()}
    </div>
</div>
