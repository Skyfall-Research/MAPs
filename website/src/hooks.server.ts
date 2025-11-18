import type { Handle } from '@sveltejs/kit';

/**
 * Server-side hooks for handling CSRF protection with multiple origins.
 *
 * This allows form submissions from both the production domain (maps.skyfall.ai)
 * and the ALB URL for testing/internal access.
 */
export const handle: Handle = async ({ event, resolve }) => {
	// List of allowed origins for form submissions
	const allowedOrigins = [
		'https://maps.skyfall.ai',
		'https://theme-park-alb-591885444.us-east-2.elb.amazonaws.com',
		// Local development origins
		'http://localhost:3001',
		'http://127.0.0.1:3001',
		'http://localhost:5173',
		'http://127.0.0.1:5173'
	];

	const origin = event.request.headers.get('origin');
	const method = event.request.method;

	// For POST/PUT/PATCH/DELETE requests with an origin header
	if (origin && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
		// Check if the origin is in our allowed list
		if (!allowedOrigins.includes(origin)) {
			// If not allowed, return 403 Forbidden
			return new Response('Cross-site request forbidden', {
				status: 403,
				headers: {
					'Content-Type': 'text/plain'
				}
			});
		}
	}

	// Continue with the request
	return resolve(event);
};
