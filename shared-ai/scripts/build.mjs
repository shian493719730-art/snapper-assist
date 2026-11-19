import {readFileSync,writeFileSync,mkdirSync,cpSync,rmSync} from 'node:fs';
rmSync('dist',{recursive:true,force:true});mkdirSync('dist/server',{recursive:true});mkdirSync('dist/.openai',{recursive:true});
let source=['methods.js','protocol.js','index.js'].map(n=>readFileSync('worker/'+n,'utf8').replace(/^import .* from .*;\n/gm,'')).join('\n');
writeFileSync('dist/server/index.js',source);cpSync('.openai/hosting.json','dist/.openai/hosting.json');cpSync('drizzle','dist/.openai/drizzle',{recursive:true});
