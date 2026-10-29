# Summarizer API

tl;dr: app summarizes Youtube stock related videos with a  RAG search for browsing historical data.

### Idea behind the project
I spend a lot of time watching YT videos about the stock market but I'm still not able to watch them all..
But luckily God gave us AI! So i made it (still making) watch it for me.

NOTE. This app is not perfect and by design will never be.
Sometimes the transcripts are the problem I can't get around: yt_dlp. It's a great library, don't get me wrong, but it downloads ai-generated transcript (youtube makes them on the fly) and often they have issues which (probably) can't be solved. Sometimes when the creator talks too fast, uses uncommon words/naming then google's ai don't understand it and make up stuff. Example: I was working on a podcast which was 100% about Applovin stock, ticker $APP. There was not a single mention about Apple $AAPL, but in the transcript sometimes there was Applovin but sometimes there was "Apple 11".

App is fully self-hosted. 

The back bone of my infrastructure.
For more details visit my second repo where i'll documenting my infra [infra_repo](https://github.com/paulmarketandtech/summarizer_infra)  
![proxmox-infra](./pics/schema_20261027_updated.excalidraw.png)

