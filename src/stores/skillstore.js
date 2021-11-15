import { writable } from 'svelte/store';

// programming languages
export const skills = writable([]);
const progLangs = [
	{ name: 'python', image: '/python.png' },
	{ name: 'java', image: '/java.png' },
	{ name: 'javascript', image: '/javascript.jpeg' },
	{ name: 'golang', image: '/golang.png' },
	{ name: 'c', image: '/clang.png' },
	{ name: 'html', image: '/html.png' },
	{ name: 'css', image: '/css.png' },
	{ name: 'jquery', image: '/jquery.jpg' },
	{ name: 'node', image: '/node.png' }
];

// frame works
const frameworksList = [
	{ name: 'vue js', image: '/vuejs.png' },
	{ name: 'svelte js', image: '/sveltejs.png' },
	{ name: 'flask', image: '/flask.png' },
	{ name: 'django', image: '/django.webp' }
];

// databases
const databaseList = [
	{ name: 'postgres', image: '/postgres.png' },
	{ name: 'mysql', image: '/mysql.png' },
	{ name: 'sqlite', image: '/sqlite.png' },
	{ name: 'redis', image: '/redis.png' }
];

// tools
const tools = [
	{ name: 'Elastic Search', image: '/elasticsearch.png' },
	{ name: 'Git', image: '/git.png' },
	{ name: 'Linux', image: '/ubuntu.jpg' },
	{ name: 'Docker', image: '/docker.png' },
	{ name: 'Nginx', image: '/nginx.jpg' }
];

const myskills = {
	'Programming Languages': progLangs,
	Frameworks: frameworksList,
	Databases: databaseList,
	Tools: tools
};

skills.set(myskills);
