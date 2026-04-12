const fs = require('fs');

const htmlContent = fs.readFileSync('/Users/computer-care/Downloads/sigma_horizon_accueil.html', 'utf-8');

const cssMatch = htmlContent.match(/<style>([\s\S]*?)<\/style>/);
let css = cssMatch ? cssMatch[1] : '';

css = css.replace(/body\s*{/g, '.home-theme {');
css = css.replace(/body::before/g, '.home-theme::before');
css = css.replace(/body::after/g, '.home-theme::after');

// The CSS for `body { min-height: 100vh; ... }` is now `.home-theme { ... }`.
// Replace `html { ... }` with something safe or keep it.
// Also fix `*` conflicting.
css = css.replace(/\*,\s*\*::before,\s*\*::after\s*{([^}]*)}/g, '.home-theme *, .home-theme *::before, .home-theme *::after {$1}');

// Convert html body to JSX
let bodyMatch = htmlContent.match(/<body>([\s\S]*?)<\/body>/);
let jsxHtml = bodyMatch ? bodyMatch[1] : '';

// remove comments
jsxHtml = jsxHtml.replace(/<!--[\s\S]*?-->/g, '');

// handle class to className
jsxHtml = jsxHtml.replace(/class=/g, 'className=');

// handle style strings to style objects. Wait, there is a style=`margin-bottom:24px` in the CTA.
jsxHtml = jsxHtml.replace(/style="margin-bottom:24px"/g, "style={{ marginBottom: '24px' }}");
jsxHtml = jsxHtml.replace(/style="top: 65%;"/g, "style={{ top: '65%' }}");
jsxHtml = jsxHtml.replace(/style="[^"]*"/g, ""); // strip others if not matching to be safe

// close unclosed tags: img, input, br, hr
jsxHtml = jsxHtml.replace(/<br>/g, '<br/>');
jsxHtml = jsxHtml.replace(/<hr>/g, '<hr/>');
jsxHtml = jsxHtml.replace(/<img(.*?)>/g, (match) => match.endsWith('/>') ? match : match.replace(/>$/, '/>'));
jsxHtml = jsxHtml.replace(/<input(.*?)>/g, (match) => match.endsWith('/>') ? match : match.replace(/>$/, '/>'));

// Fix some SVGs or other attributes: stroke-width, stroke-linecap, stroke-linejoin -> camelCase
jsxHtml = jsxHtml.replace(/stroke-width/g, 'strokeWidth');
jsxHtml = jsxHtml.replace(/stroke-linecap/g, 'strokeLinecap');
jsxHtml = jsxHtml.replace(/stroke-linejoin/g, 'strokeLinejoin');

// Update links:
jsxHtml = jsxHtml.replace(/href="#"/g, 'href="/connexion"');

const pageContent = `
import './home.css';
import Head from 'next/head';

export default function Home() {
  return (
    <div className="home-theme">
      <link rel="preconnect" href="https://fonts.googleapis.com"/>
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous"/>
      <link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap" rel="stylesheet"/>
      ${jsxHtml}
    </div>
  );
}
`;

fs.writeFileSync('/Users/computer-care/horizon_frontend/app/home.css', css);
fs.writeFileSync('/Users/computer-care/horizon_frontend/app/page.tsx', pageContent);

console.log("Translation done");
