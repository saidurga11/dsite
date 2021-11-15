<script>
	export let skillData = { name: 'Python', image: '../static/python.png' };
</script>

<div class="w-full bg-gray-900 rounded-lg sahdow-lg p-12 flex flex-col justify-center items-center">
	<div class="mb-8">
		<img
			class="object-center object-cover rounded-full h-24 w-24"
			src={skillData.image}
			alt="image"
		/>
	</div>
	<div class="text-center">
		<p class="text-xl text-white font-bold mb-2">{skillData.name}</p>
	</div>
</div>
