<script>
	// import { programmingLangs } from '../stores/skillstore.js';
	import { skills } from '../stores/skillstore.js';
	import Skillcard from '../components/skillcard.svelte';
</script>

<div class="items-center justify-center mx-40 my-3">
	{#each Object.entries($skills) as [category, skillList]}
		<div>
			<h3 class="font-bold underline m-5 text-2xl">{category}</h3>
			<div class="grid grid-cols-5 gap-5">
				{#each skillList as skill (skill.name)}
					<Skillcard skillData={skill} />
				{/each}
			</div>
		</div>
	{/each}
	<!-- <h3 class="font-bold underline m-5 text-2xl">Programming Languages</h3>
	<div class="grid grid-cols-5 gap-5">
		{#each $programmingLangs as lang (lang.name)}
			<Skillcard skillData={lang} />
		{/each}
	</div>

	<h3 class="font-bold underline text-2xl m-5">Frameworks</h3>
	<div class="grid grid-cols-5 gap-5">
		{#each $frameworks as framework (framework.name)}
			<Skillcard skillData={framework} />
		{/each}
	</div> -->
</div>
