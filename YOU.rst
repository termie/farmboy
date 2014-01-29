

You are a developer at a company that produces a service made up of multiple
components. You are one of many, each similar in their uniqueness, much like
the components of your service.

You are smart, as are your coworkers, so you use a pretty common overall
architecture for your service. Your service has:

  * A a web component that accepts incoming API requests from, hopefully,
    many users.
  * A background task component that processes incoming data to provide
    a, hopefully, valuable service to your users.
  * A load balancer to distribute incoming requests across multiple web
    components.
  * A database component that provides persistent and common storage for
    your other components.

You are concerned with security, and therefore network access between these
hosts is limited. Your simple network configuration looks like:

  * Publicly accessible port 80 and 443 on your load balancer.
  * Web components accept access from the load balancer on port 80.
  * Background tasks accept access from the web components on custom ports.
  * Database components accept access from the web components and background
    task components on a custom port.
  * When doing development, all those servers accept connections on port 22
    for SSH connections.

You usually are working on one component of this service at a time, probably
the web component or background task components, but every week or so you make
sure to update the rest of your components to make sure you are compatible
with and taking advantage of changes made by other developers.

You would like your changes to take the minimum amount of time to be reflected
in your development environment. You would like to rebuild servers, databases,
and caches as infrequently as possible but be able to do so easily when
required.

You don't want to have your hands tied while debugging the components you are
working on. You want to be able to make ridiculous hacks to get at the
information you need quickly. You want to laugh with your coworkers about the
terrible, frightening genius that was required to come up with those hacks.
