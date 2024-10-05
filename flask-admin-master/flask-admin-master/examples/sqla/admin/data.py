from admin import db
from admin.models import User, Post, Tag, Tree, AVAILABLE_USER_TYPES
import random
import datetime


def build_sample_db():
    """
    Populate a small db with some example entries.
    """

    db.drop_all()
    db.create_all()

    # Create sample Users
    first_names = [
        'Harry', 'Amelia', 'Oliver', 'Jack', 'Isabella', 'Charlie', 'Sophie', 'Mia',
        'Jacob', 'Thomas', 'Emily', 'Lily', 'Ava', 'Isla', 'Alfie', 'Olivia', 'Jessica',
        'Riley', 'William', 'James', 'Geoffrey', 'Lisa', 'Benjamin', 'Stacey', 'Lucy'
    ]
    last_names = [
        'Brown', 'Brown', 'Patel', 'Jones', 'Williams', 'Johnson', 'Taylor', 'Thomas',
        'Roberts', 'Khan', 'Clarke', 'Clarke', 'Clarke', 'James', 'Phillips', 'Wilson',
        'Ali', 'Mason', 'Mitchell', 'Rose', 'Davis', 'Davies', 'Rodriguez', 'Cox', 'Alexander'
    ]

    countries = [
        ("ZA", "South Africa", 27, "ZAR", "Africa/Johannesburg"),
        ("BF", "Burkina Faso", 226, "XOF", "Africa/Ouagadougou"),
        ("US", "United States of America", 1, "USD", "America/New_York"),
        ("BR", "Brazil", 55, "BRL", "America/Sao_Paulo"),
        ("TZ", "Tanzania", 255, "TZS", "Africa/Dar_es_Salaam"),
        ("DE", "Germany", 49, "EUR", "Europe/Berlin"),
        ("CN", "China", 86, "CNY", "Asia/Shanghai"),
    ]

    user_list = []
    for i in range(len(first_names)):
        user = User()
        country = random.choice(countries)
        user.type = random.choice(AVAILABLE_USER_TYPES)[0]
        user.first_name = first_names[i]
        user.last_name = last_names[i]
        user.email = first_names[i].lower() + "@example.com"

        user.website = "https://www.example.com"
        user.ip_address = "127.0.0.1"

        user.coutry = country[1]
        user.currency = country[3]
        user.timezone = country[4]

        user.dialling_code = country[2]
        user.local_phone_number = '0' + ''.join(random.choices('123456789', k=9))

        user_list.append(user)
        db.session.add(user)

    # Create sample Tags
    tag_list = []
    for tmp in ["YELLOW", "WHITE", "BLUE", "GREEN", "RED", "BLACK", "BROWN", "PURPLE", "ORANGE"]:
        tag = Tag()
        tag.name = tmp
        tag_list.append(tag)
        db.session.add(tag)

    # Create sample Posts
    sample_text = [
        {
            'title': "de Finibus Bonorum et Malorum - Part I",
            'content': "Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor \
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud \
exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure \
dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. \
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt \
mollit anim id est laborum."
        },
        {
            'title': "de Finibus Bonorum et Malorum - Part II",
            'content': "Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque \
laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto \
beatae vitae dicta sunt explicabo. Nemo enim ipsam voluptatem quia voluptas sit aspernatur \
aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi \
nesciunt. Neque porro quisquam est, qui dolorem ipsum quia dolor sit amet, consectetur, \
adipisci velit, sed quia non numquam eius modi tempora incidunt ut labore et dolore magnam \
aliquam quaerat voluptatem. Ut enim ad minima veniam, quis nostrum exercitationem ullam \
corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur? Quis autem vel eum \
iure reprehenderit qui in ea voluptate velit esse quam nihil molestiae consequatur, vel illum \
qui dolorem eum fugiat quo voluptas nulla pariatur?"
        },
        {
            'title': "de Finibus Bonorum et Malorum - Part III",
            'content': "At vero eos et accusamus et iusto odio dignissimos ducimus qui blanditiis praesentium \
voluptatum deleniti atque corrupti quos dolores et quas molestias excepturi sint occaecati \
cupiditate non provident, similique sunt in culpa qui officia deserunt mollitia animi, id \
est laborum et dolorum fuga. Et harum quidem rerum facilis est et expedita distinctio. Nam \
libero tempore, cum soluta nobis est eligendi optio cumque nihil impedit quo minus id quod \
maxime placeat facere possimus, omnis voluptas assumenda est, omnis dolor repellendus. \
Temporibus autem quibusdam et aut officiis debitis aut rerum necessitatibus saepe eveniet \
ut et voluptates repudiandae sint et molestiae non recusandae. Itaque earum rerum hic tenetur \
a sapiente delectus, ut aut reiciendis voluptatibus maiores alias consequatur aut perferendis \
doloribus asperiores repellat."
        }
    ]

    for user in user_list:
        entry = random.choice(sample_text)  # select text at random
        post = Post()
        post.user = user
        post.title = "{}'s opinion on {}".format(user.first_name, entry['title'])
        post.text = entry['content']
        post.background_color = random.choice(["#cccccc", "red", "lightblue", "#0f0"])
        tmp = int(1000 * random.random())  # random number between 0 and 1000:
        post.date = datetime.datetime.now() - datetime.timedelta(days=tmp)
        post.tags = random.sample(tag_list, 2)  # select a couple of tags at random
        db.session.add(post)

    # Create a sample Tree structure
    trunk = Tree(name="Trunk")
    db.session.add(trunk)
    for i in range(5):
        branch = Tree()
        branch.name = "Branch " + str(i + 1)
        branch.parent = trunk
        db.session.add(branch)
        for j in range(5):
            leaf = Tree()
            leaf.name = "Leaf " + str(j + 1)
            leaf.parent = branch
            db.session.add(leaf)

    db.session.commit()
    return
