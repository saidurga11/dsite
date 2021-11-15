<!-- This example requires Tailwind CSS v2.0+ -->
<script>
	let routesList = [
		{ displayName: 'Dashboard', routeName: '' },
		{ displayName: 'Projects', routeName: 'projects' },
		{ displayName: 'Blog', routeName: 'blog' },
		{ displayName: 'Tech', routeName: 'tech' },
		{ displayName: 'Contact', routeName: 'contact' }
	];
	let activeRoute = routesList[0].routeName;
</script>

<nav class="bg-gray-800">
	<div class="max-w-7xl mx-auto px-2 sm:px-6 lg:px-8">
		<div class="relative flex items-center justify-between h-16">
			<div class="absolute inset-y-0 left-0 flex sm:hidden">
				<!-- Mobile menu button-->
				<button
					type="button"
					class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
					aria-controls="mobile-menu"
					aria-expanded="false"
				>
					<span class="sr-only">Open main menu</span>
					<!--
            Icon when menu is closed.

            Heroicon name: outline/menu

            Menu open: "hidden", Menu closed: "block"
          -->
					<svg
						class="block h-6 w-6"
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
						aria-hidden="true"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M4 6h16M4 12h16M4 18h16"
						/>
					</svg>
					<svg
						class="hidden h-6 w-6"
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
						aria-hidden="true"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>
			<h4 class="font-bold text-white text-3xl m-x-3">DSite</h4>
			<div class="flex-1 flex items-center justify-center sm:items-stretch sm:justify-start">
				<!-- <div class="flex-shrink-0 flex items-center">
				</div> -->
				<div class="hidden w-full sm:block sm:ml-6">
					<div class="flex space-x-4 justify-end">
						{#each routesList as route}
							<a
								href="/{route.routeName}"
								class="text-gray-300 hover:bg-gray-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium"
								class:selected={activeRoute === route.routeName}
								on:click={() => {
									activeRoute = route.routeName;
								}}
							>
								{route.displayName}
							</a>
						{/each}
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Mobile menu, show/hide based on menu state. -->
	<div class="sm:hidden" id="mobile-menu">
		<div class="px-2 pt-2 pb-3 space-y-1">
			<!-- Current: "bg-gray-900 text-white", Default: "text-gray-300 hover:bg-gray-700 hover:text-white" -->
			{#each routesList as route}
				<a
					href="/{route.routeName}"
					class="text-gray-300 hover:bg-gray-700 hover:text-white block px-3 py-2 rounded-md text-base font-medium"
					class:selected={route.routeName === activeRoute}
					on:click={() => {
						activeRoute = route.routeName;
					}}
				>
					{route.displayName}
				</a>
			{/each}
		</div>
	</div>
</nav>

<style>
	.selected {
		background-color: black;
		color: whitesmoke;
	}
</style>
