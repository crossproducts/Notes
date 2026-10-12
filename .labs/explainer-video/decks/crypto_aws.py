"""Certificates, mTLS, envelope encryption and HSMs -- and how AWS does them.

One story told in order: how do you prove who you are, and protect a secret,
when the network between you is hostile. Every abstract idea is anchored to a
physical one (passport, padlock, locked box, bank vault) because that is what
makes it stick.
"""

TITLE = "Certificates, mTLS, Envelope Encryption & HSMs on AWS"
SLUG = "certificates-mtls-kms"
VOICE = "am_michael"          # kokoro; ignored by --engine sapi

SCENES = [
    # ------------------------------------------------------------ 00 title --
    {
        "narration":
            "Certificates. Mutual T L S. Envelope encryption. Hardware security "
            "modules. Four things that sound separate, but they are really one "
            "story, and it has two halves: how do you prove who you are, and how "
            "do you protect a secret, when the network in between cannot be "
            "trusted. Let's build it from the bottom up.",
        "html": """
          <div class='kicker'>A ground-up explainer</div>
          <h1>Certificates, mTLS,<br>Envelope Encryption &amp; HSMs</h1>
          <div class='sub'>Two questions, one story:<br>
            <b>Who are you?</b> &nbsp;&middot;&nbsp; <b>How do I keep this secret?</b></div>
          <div class='row'>
            <div class='card b-blue'><p class='blue'>PART ONE</p><h3>Proving identity</h3>
              <p>Keys &rarr; certificates &rarr; TLS &rarr; mTLS</p></div>
            <div class='card b-green'><p class='green'>PART TWO</p><h3>Protecting secrets</h3>
              <p>Envelope encryption &rarr; HSMs</p></div>
            <div class='card b-amber'><p class='amber'>PART THREE</p><h3>On AWS</h3>
              <p>ACM &middot; Private CA &middot; KMS &middot; CloudHSM</p></div>
          </div>""",
    },
    # ---------------------------------------------------------- 01 problem --
    {
        "narration":
            "Here is the whole problem in one picture. Two machines want to talk. "
            "Everything in between is hostile: the public internet, somebody "
            "else's router, a proxy you do not control. An attacker there can do "
            "two different things. They can read what goes past. And, much worse, "
            "they can pretend to be the other side. Encryption alone only solves "
            "the first one.",
        "html": """
          <div class='kicker'>The problem</div>
          <h2>You cannot trust the wire</h2>
          <div class='row center'>
            <div class='card b-blue' style='max-width:380px'><p class='blue'>YOU</p>
              <h3>Client</h3><p>wants to send something private</p></div>
            <div class='arrow'>&rarr;</div>
            <div class='card b-red'><p class='red'>THE NETWORK</p>
              <h3>Hostile by default</h3>
              <p><b style='color:#F2777A'>Reads</b> what passes &mdash; solved by encryption<br>
                 <b style='color:#F2777A'>Impersonates</b> either end &mdash; <b>not</b> solved by encryption</p></div>
            <div class='arrow'>&rarr;</div>
            <div class='card b-blue' style='max-width:380px'><p class='blue'>THEM</p>
              <h3>Server</h3><p>...or someone claiming to be</p></div>
          </div>
          <div class='note'>Encrypting to an impostor is still encrypting to an impostor.</div>""",
    },
    # ------------------------------------------------------------- 02 keys --
    {
        "narration":
            "Start with the one building block everything else rests on: a key "
            "pair. Think of it as padlocks and a key. You stamp out open padlocks "
            "and hand them to anybody who asks. That is your public key. You keep "
            "the single key that opens them, and you never give it away. That is "
            "your private key. Anyone can snap a padlock shut on a message to "
            "you. Only you can open it.",
        "html": """
          <div class='kicker'>Building block</div>
          <h2>A key pair is padlocks and a key</h2>
          <div class='row'>
            <div class='card b-green'><p class='green'>PUBLIC KEY</p><h3>The open padlock</h3>
              <p>Hand it to anyone. Publish it. It is not a secret &mdash; that is
                 the entire point of it.</p></div>
            <div class='card b-red'><p class='red'>PRIVATE KEY</p><h3>The only key</h3>
              <p>Never leaves you. Everything in this video is ultimately about
                 keeping this one thing from moving.</p></div>
          </div>
          <div class='analogy'>Anyone can lock it. Only you can open it.</div>""",
    },
    # ------------------------------------------------------- 03 signatures --
    {
        "narration":
            "And it runs in reverse, which is the part people miss. If something "
            "can be opened with your public padlock, then it must have been "
            "locked with your private key, and only you have that. So running it "
            "backwards does not hide anything at all. It proves authorship. That "
            "is a digital signature, and the rest of this video is built on it.",
        "html": """
          <div class='kicker'>The same maths, run backwards</div>
          <h2>Forwards hides. Backwards <span class='amber'>proves</span>.</h2>
          <div class='row'>
            <div class='card b-blue'><p class='blue'>FORWARDS &mdash; ENCRYPT</p>
              <p class='kv'>lock with <b>their public</b> key<br>
                 open with <b>their private</b> key<br><br>
                 &rarr; only they can read it</p></div>
            <div class='card b-amber'><p class='amber'>BACKWARDS &mdash; SIGN</p>
              <p class='kv'>lock with <b>my private</b> key<br>
                 open with <b>my public</b> key<br><br>
                 &rarr; it hides nothing, but <b>only I could have made it</b></p></div>
          </div>
          <div class='note'>A signature is not secrecy. It is proof of authorship
            that anyone can check.</div>""",
    },
    # -------------------------------------------------------- 04 impostor --
    {
        "narration":
            "But hold on. A padlock on its own proves nothing about who you are. "
            "I can stamp out padlocks too, and tell you they belong to your bank. "
            "You have no way to tell mine from theirs. That single gap is the "
            "entire reason certificates exist.",
        "html": """
          <div class='kicker'>The gap</div>
          <h2>A key proves nothing about <span class='red'>who</span> you are</h2>
          <div class='row center'>
            <div class='card b-green'><h3>"I'm your bank"</h3>
              <p class='mono'>public key: 3048 0241 00C9...</p></div>
            <div class='card b-red'><h3>"No, <i>I'm</i> your bank"</h3>
              <p class='mono'>public key: 3048 0241 00A7...</p></div>
          </div>
          <div class='analogy'>Both are real keys. Both work perfectly.
            Nothing in the maths says which one is the bank.</div>
          <div class='note'>You need someone you already trust to vouch. That is a
            certificate.</div>""",
    },
    # ------------------------------------------------------ 05 certificate --
    {
        "narration":
            "A certificate is a passport. It is a small document that says: this "
            "name goes with this public key, it is valid between these dates, and "
            "here is who issued it. And then the issuer signs the whole thing "
            "with their private key. Here is the thing to hold on to: you do not "
            "trust the passport. You trust the signature on it. Forging the "
            "document is trivial. Forging that signature is not.",
        "html": """
          <div class='kicker'>The fix</div>
          <h2>A certificate is a <span class='amber'>passport</span></h2>
          <div class='row'>
            <div class='card b-amber' style='flex:1.25'>
              <p class='amber'>X.509 CERTIFICATE</p>
              <p class='kv'>
                <b>Subject</b> &nbsp; CN = api.example.com<br>
                <b>Public key</b> &nbsp; 3048 0241 00C9 ...<br>
                <b>Valid</b> &nbsp; 2026-01-14 &rarr; 2027-02-11<br>
                <b>Issuer</b> &nbsp; CN = Example Intermediate CA<br>
                <b style='color:#F0B429'>Signature</b> &nbsp; <span class='mono'>9f2a 71c4 ...</span></p>
            </div>
            <div class='card b-blue'><h3>What makes it work</h3>
              <p>Anyone can <i>write</i> this document.<br><br>
                 Only the issuing authority can produce that last line &mdash; and
                 you can check it with the issuer's public key.</p></div>
          </div>
          <div class='analogy'>You don't trust the passport. You trust the office
            that stamped it.</div>""",
    },
    # ------------------------------------------------------------ 06 chain --
    {
        "narration":
            "Trust is then delegated down a chain. Your laptop has never heard of "
            "my server, and it never will. What it does have is a store of root "
            "authorities, shipped with the operating system. A root vouches for an "
            "intermediate. The intermediate vouches for my server. Your laptop "
            "checks each signature up the chain until it lands on a root it "
            "already trusts. That is the entire trust model of the internet, and "
            "it is why an expired or self-signed certificate makes your browser "
            "shout: the chain does not reach anything it knows.",
        "html": """
          <div class='kicker'>Delegation</div>
          <h2>The chain of trust</h2>
          <div class='row center'>
            <div class='card b-green'><p class='green'>PRE-TRUSTED</p><h3>Root CA</h3>
              <p>Already in your OS / browser trust store. Offline, heavily
                 guarded, lasts decades.</p></div>
            <div class='arrow'>signs &rarr;</div>
            <div class='card b-blue'><p class='blue'>DELEGATE</p><h3>Intermediate CA</h3>
              <p>Does the day-to-day issuing, so the root can stay offline.</p></div>
            <div class='arrow'>signs &rarr;</div>
            <div class='card b-amber'><p class='amber'>YOURS</p><h3>Leaf certificate</h3>
              <p>api.example.com &mdash; short-lived, auto-renewed.</p></div>
          </div>
          <div class='note'>Verification walks right to left and stops at the first
            thing it already trusts. No root at the end &rarr; browser warning.</div>""",
    },
    # -------------------------------------------------------------- 07 TLS --
    {
        "narration":
            "So here is ordinary H T T P S, and notice that it is lopsided. The "
            "server presents its certificate and you verify it. You present "
            "nothing. The server has no idea who you are, which is exactly why "
            "the very next thing you do is type a password. Identity in one "
            "direction is handled by cryptography. In the other direction it is "
            "handled by a secret you have to remember and the server has to store.",
        "html": """
          <div class='kicker'>Ordinary HTTPS</div>
          <h2>TLS proves <span class='amber'>one</span> side</h2>
          <div class='row center'>
            <div class='card b-blue'><h3>Client</h3>
              <p>&#10003; verifies the server's certificate<br>
                 &#10007; presents nothing<br><br>
                 <span class='pill grey'>identity: unknown</span></p></div>
            <div class='arrow'>&harr;</div>
            <div class='card b-green'><h3>Server</h3>
              <p>&#10003; presents its certificate<br>
                 &#10007; learns nothing about you<br><br>
                 <span class='pill green'>identity: proven</span></p></div>
          </div>
          <div class='analogy'>Like walking into a shop: you can check their licence
            on the wall. They have no idea who you are.</div>
          <div class='note'>Hence passwords, API keys, bearer tokens &mdash; all of
            them shared secrets, all of them stealable.</div>""",
    },
    # ------------------------------------------------------------- 08 mTLS --
    {
        "narration":
            "Mutual T L S just makes it symmetric. Both ends present a "
            "certificate. Both ends verify the other against a trust store. Now "
            "the connection itself proves identity in both directions, and there "
            "is no password anywhere in the picture. This is how services "
            "authenticate to each other when there is no human present to log in. "
            "Think of a secure facility: the guard checks your badge, and you "
            "check the guard's.",
        "html": """
          <div class='kicker'>The symmetric version</div>
          <h2>mTLS proves <span class='green'>both</span> sides</h2>
          <div class='row center'>
            <div class='card b-green'><h3>Service A</h3>
              <p>&#10003; presents its certificate<br>
                 &#10003; verifies B against the trust store<br><br>
                 <span class='pill green'>identity: proven</span></p></div>
            <div class='arrow'>&harr;</div>
            <div class='card b-green'><h3>Service B</h3>
              <p>&#10003; presents its certificate<br>
                 &#10003; verifies A against the trust store<br><br>
                 <span class='pill green'>identity: proven</span></p></div>
          </div>
          <div class='analogy'>The guard checks your badge &mdash; and you check
            the guard's.</div>
          <div class='note'>No password. No API key. Nothing in an environment
            variable waiting to be leaked.</div>""",
    },
    # -------------------------------------------------------- 09 why mTLS --
    {
        "narration":
            "And here is why that is worth the trouble. A stolen A P I key works "
            "from anywhere on earth the moment it leaks, because it is just a "
            "string. A stolen certificate is useless on its own, because the "
            "certificate is public. The attacker needs the matching private key as "
            "well. And if that private key was generated inside hardware and "
            "cannot be exported, there is nothing to steal. Which takes us "
            "straight into the second half of the story.",
        "html": """
          <div class='kicker'>Why bother</div>
          <h2>A secret you can copy versus one you cannot</h2>
          <div class='row'>
            <div class='card b-red'><p class='red'>SHARED SECRET</p>
              <h3>API key / password</h3>
              <p>A string. Copy it once and it works from anywhere, forever,
                 until someone notices and rotates it.</p>
              <div style='margin-top:18px'><span class='pill red'>copyable</span></div></div>
            <div class='card b-green'><p class='green'>ASYMMETRIC IDENTITY</p>
              <h3>Certificate + private key</h3>
              <p>The certificate is public and worthless alone. The private key
                 never travels &mdash; and in hardware, it physically cannot.</p>
              <div style='margin-top:18px'><span class='pill green'>not copyable</span></div></div>
          </div>
          <div class='note'>So: how do you keep a key from ever moving? Part two.</div>""",
    },
    # ------------------------------------------------------- 10 bulk problem --
    {
        "narration":
            "Switch problems. You now have a terabyte of data to encrypt. You have "
            "one well-guarded master key. There are two obvious approaches and "
            "both are bad. Send the terabyte to the master key, and you are "
            "throttled by a service designed for small operations. Or copy the "
            "master key out to where the data is, and you have just destroyed the "
            "thing that made it safe. Envelope encryption is the way between them.",
        "html": """
          <div class='kicker'>A different problem</div>
          <h2>You have 1 TB and one precious key</h2>
          <div class='row'>
            <div class='card b-red'><p class='red'>OPTION A</p>
              <h3>Send the data to the key</h3>
              <p>Every byte through a service built for small, audited operations.
                 Slow, expensive, and it will rate-limit you.</p></div>
            <div class='card b-red'><p class='red'>OPTION B</p>
              <h3>Send the key to the data</h3>
              <p>Now the master key is on disk, in memory, in a log, in a core
                 dump. You have thrown away the only thing protecting everything.</p></div>
          </div>
          <div class='analogy'>Move the data, or move the key. Both are wrong.</div>""",
    },
    # ---------------------------------------------------------- 11 envelope --
    {
        "narration":
            "So you do neither, and this is the genuinely elegant bit. Generate a "
            "brand new random key just for this one piece of data. Call it the "
            "data key. Encrypt the data with it locally, using fast symmetric "
            "crypto. Then hand only that tiny data key to the master key to be "
            "encrypted, and wipe the plaintext copy from memory. Store the "
            "encrypted data and the encrypted data key side by side. That pairing "
            "is the envelope. You locked your documents in a box, then locked the "
            "box's key inside a vault. You can now ship that box anywhere in the "
            "world, with its own locked key taped to the lid, and it is useless to "
            "anyone who cannot open the vault.",
        "html": """
          <div class='kicker'>The trick</div>
          <h2>Envelope encryption</h2>
          <div class='row'>
            <div class='card b-blue' style='flex:0.8'><p class='blue'>1</p>
              <h3>New data key</h3><p>Random, single-use, generated per object.</p></div>
            <div class='arrow'>&rarr;</div>
            <div class='card b-green' style='flex:1.1'><p class='green'>2</p>
              <h3>Encrypt the data locally</h3>
              <p>Fast symmetric AES. The 1 TB never leaves your machine.</p></div>
            <div class='arrow'>&rarr;</div>
            <div class='card b-amber' style='flex:1.1'><p class='amber'>3</p>
              <h3>Wrap the data key</h3>
              <p>Only the small key goes to the master key. Then wipe the
                 plaintext copy.</p></div>
          </div>
          <div class='row'>
            <div class='card b-purple' style='min-height:0'><p class='purple'>STORED TOGETHER &mdash; THE ENVELOPE</p>
              <p class='mono' style='font-size:30px'>[ encrypted data ] + [ encrypted data key ]</p></div>
          </div>
          <div class='analogy'>Documents in a box. The box's key, locked in the vault.</div>""",
    },
    # --------------------------------------------------------- 12 why good --
    {
        "narration":
            "Three wins, and you get all of them at once. Speed, because the bulk "
            "work is fast local symmetric crypto and only a few hundred bytes ever "
            "touch the master key. Blast radius, because every object gets its own "
            "data key, so one compromised key exposes exactly one object. And "
            "rotation, which is the one people underestimate: to rotate the master "
            "key you only re-wrap the small keys. You never re-encrypt the "
            "petabyte.",
        "html": """
          <div class='kicker'>Why it is the standard</div>
          <h2>Three wins at once</h2>
          <div class='row'>
            <div class='card b-green'><p class='green'>SPEED</p><h3>Local and symmetric</h3>
              <p>Bulk data never leaves the machine. Only ~32 bytes make the
                 network round trip.</p></div>
            <div class='card b-blue'><p class='blue'>BLAST RADIUS</p><h3>One key per object</h3>
              <p>A leaked data key exposes that object and nothing else. Not the
                 bucket. Not the database.</p></div>
            <div class='card b-amber'><p class='amber'>ROTATION</p><h3>Re-wrap, don't re-encrypt</h3>
              <p>Rotating the master touches a few hundred bytes of wrapped keys,
                 not a petabyte of data.</p></div>
          </div>""",
    },
    # -------------------------------------------------------------- 13 HSM --
    {
        "narration":
            "Which leaves one question. Where does the master key actually live? "
            "In a hardware security module. A dedicated, tamper-resistant device "
            "with a deliberately limited job. Keys are generated inside it and "
            "there is no command, for anyone at any privilege level, that exports "
            "one. You send data in and get a result out; the key itself never "
            "crosses the boundary. Try to physically open it and it wipes itself. "
            "That behaviour is certified under F I P S one-forty dash three. It is "
            "a safe that destroys the contents if you drill it.",
        "html": """
          <div class='kicker'>Where the master key lives</div>
          <h2>An HSM is the <span class='amber'>vault</span></h2>
          <div class='row center'>
            <div class='card b-blue' style='flex:0.9'><h3>In</h3>
              <p class='mono'>encrypt(data_key)<br>decrypt(blob)<br>sign(digest)</p></div>
            <div class='arrow'>&rarr;</div>
            <div class='card b-amber' style='flex:1.3'><p class='amber'>HARDWARE BOUNDARY</p>
              <h3>Key generated inside.<br>No export path. At all.</h3>
              <p>Tamper-resistant and tamper-evident &mdash; physical attack
                 triggers zeroisation. Certified FIPS 140-3.</p></div>
            <div class='arrow'>&rarr;</div>
            <div class='card b-green' style='flex:0.9'><h3>Out</h3>
              <p class='mono'>results only<br><br><span style='color:#F2777A'>never the key</span></p></div>
          </div>
          <div class='analogy'>A safe that burns the contents if you drill it.</div>""",
    },
    # ------------------------------------------------------------- 14 KMS --
    {
        "narration":
            "On A W S, that vault is K M S, and the whole pattern collapses into "
            "two API calls. You call Generate Data Key, and it hands you back two "
            "things: a plaintext data key, and an encrypted copy of that same key. "
            "You encrypt your object locally with the plaintext one, store the "
            "encrypted one next to the result, and wipe the plaintext from memory. "
            "To read it back later you send the encrypted key to Decrypt and get "
            "the plaintext back for a moment. Your K M S key never leaves K M S at "
            "any point. And this is not something you usually write yourself: S "
            "three, E B S, R D S and Secrets Manager all do exactly this for you.",
        "html": """
          <div class='kicker'>On AWS &mdash; the engine</div>
          <h2>KMS is envelope encryption as two API calls</h2>
          <div class='row center'>
            <div class='card b-amber' style='flex:0.9'><p class='amber'>KMS KEY</p>
              <h3>Never leaves</h3><p>Multi-tenant, FIPS-validated hardware. You hold
                a reference, never the bytes.</p></div>
            <div class='arrow'>&rarr;</div>
            <div class='card b-blue' style='flex:1.2'><p class='blue'>WRITE</p>
              <h3 class='mono' style='font-size:28px'>GenerateDataKey</h3>
              <p class='kv'>returns <b>plaintext key</b> &rarr; encrypt locally, then wipe<br>
                 returns <b>encrypted key</b> &rarr; store beside the ciphertext</p></div>
            <div class='arrow'>&rarr;</div>
            <div class='card b-green' style='flex:1.2'><p class='green'>READ</p>
              <h3 class='mono' style='font-size:28px'>Decrypt</h3>
              <p class='kv'>send the <b>encrypted key</b><br>
                 get the <b>plaintext key</b> back briefly, unwrap, wipe</p></div>
          </div>
          <div class='note'>S3 SSE-KMS, EBS, RDS and Secrets Manager are all doing
            precisely this on your behalf.</div>""",
    },
    # ------------------------------------------------- 15 ACM / private CA --
    {
        "narration":
            "Back to identity. For public certificates A W S gives you A C M, "
            "which issues them free, renews them automatically, and never exposes "
            "the private key to you at all: it is generated for, and bound to, "
            "your load balancer or CloudFront distribution. For internal identity "
            "you run A W S Private C A, which is your own certificate authority "
            "for issuing short-lived certificates to your own services. And then "
            "both Application Load Balancer and A P I Gateway can do the mutual T "
            "L S check for you at the edge: you put a trust store in S three, and "
            "they verify client certificates before your code ever sees the "
            "request.",
        "html": """
          <div class='kicker'>On AWS &mdash; identity</div>
          <h2>ACM, Private CA, and mTLS at the edge</h2>
          <div class='row'>
            <div class='card b-blue'><p class='blue'>PUBLIC CERTS</p><h3>ACM</h3>
              <p>Free, auto-renewing. The private key is generated for the
                 endpoint and is never exported to you &mdash; so it cannot leak
                 through you.</p>
              <p class='mono' style='margin-top:14px'>ALB &middot; CloudFront &middot; API GW</p></div>
            <div class='card b-green'><p class='green'>INTERNAL IDENTITY</p><h3>AWS Private CA</h3>
              <p>Your own root and intermediates. Issues the short-lived certs
                 your services present to each other.</p>
              <p class='mono' style='margin-top:14px'>EKS &middot; ECS &middot; IoT</p></div>
            <div class='card b-amber'><p class='amber'>mTLS, MANAGED</p><h3>Trust store in S3</h3>
              <p>ALB and API Gateway verify the client certificate at the edge.
                 Your application receives an already-authenticated request.</p></div>
          </div>""",
    },
    # ------------------------------------------------------- 16 CloudHSM --
    {
        "narration":
            "And when the shared model is not enough, there is one more step. K M "
            "S is multi-tenant: excellent, cheap, deeply integrated, but the "
            "hardware is shared. If you have a compliance rule demanding "
            "single-tenant hardware, or you must be able to say you hold the only "
            "copy of a key, Cloud H S M gives you dedicated F I P S one-forty dash "
            "three level three modules in your own V P C. The sweet spot between "
            "the two is a K M S custom key store: you keep the familiar K M S A P "
            "I and all the I A M integration, but the keys physically live in your "
            "own Cloud H S M cluster.",
        "html": """
          <div class='kicker'>On AWS &mdash; how much vault do you need</div>
          <h2>KMS, CloudHSM, or both</h2>
          <div class='row'>
            <div class='card b-blue'><p class='blue'>DEFAULT</p><h3>KMS</h3>
              <p>Multi-tenant managed hardware. Cheap, integrated with every
                 service and with IAM. <b>Right answer almost always.</b></p></div>
            <div class='card b-amber'><p class='amber'>WHEN YOU MUST</p><h3>CloudHSM</h3>
              <p>Dedicated single-tenant FIPS 140-3 Level 3 modules in your VPC.
                 You administer them &mdash; and you can lose the keys.</p></div>
            <div class='card b-green'><p class='green'>THE BRIDGE</p><h3>KMS custom key store</h3>
              <p>KMS API and IAM on the front. Your own CloudHSM cluster holding
                 the actual keys at the back.</p></div>
          </div>
          <div class='note'>Pick CloudHSM because a regulator requires it &mdash;
            not because it sounds safer.</div>""",
    },
    # ------------------------------------------------------------ 17 recap --
    {
        "narration":
            "So, the whole thing in five lines. A certificate proves identity "
            "because somebody you already trust signed it. Mutual T L S makes that "
            "proof run both ways, so services can authenticate with no shared "
            "secret to steal. Envelope encryption protects bulk data with a "
            "disposable key, wrapped by a master key that never moves. An H S M is "
            "the hardware that makes never moves physically true rather than just "
            "a policy. And on A W S: A C M and Private C A for identity, K M S for "
            "the envelope, Cloud H S M when the vault has to be yours alone. "
            "Everything else in this space is a detail hanging off one of those "
            "five sentences.",
        "html": """
          <div class='kicker'>The whole thing</div>
          <h2>Five sentences</h2>
          <ul>
            <li><b>Certificate</b> &mdash; identity, because someone you already
                trust signed it. <span class='grey'>A passport.</span></li>
            <li><b>mTLS</b> &mdash; that proof, both directions, so there is no
                shared secret to steal. <span class='grey'>Both sides show a badge.</span></li>
            <li><b>Envelope encryption</b> &mdash; a disposable key for the data,
                wrapped by a master that never moves. <span class='grey'>Box in a vault.</span></li>
            <li><b>HSM</b> &mdash; the hardware that makes "never moves" physical
                rather than a policy. <span class='grey'>A safe that self-destructs.</span></li>
            <li><b>On AWS</b> &mdash; ACM and Private CA for identity, KMS for the
                envelope, CloudHSM when the vault must be yours.</li>
          </ul>
          <div class='note'>Everything else is a detail hanging off one of these.</div>""",
    },
]
