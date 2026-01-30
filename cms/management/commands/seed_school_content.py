"""
Management command to seed the database with St. Vincent Pallotti School content.

This command creates:
- Navigation menus (hierarchical structure)
- Pages with detailed content
- Sections for each page with JSON content

Usage:
    python manage.py seed_school_content [--school-slug SLUG] [--overwrite]
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify
from tenants.models import School, Organization
from cms.models import NavigationMenu, Page, Section


# Complete content data extracted from stvincent.md
SCHOOL_CONTENT = {
    "home": {
        "title": "Home",
        "slug": "home",
        "description": "Welcome to St. Vincent Pallotti School, Korba",
        "sections": {
            "about": {
                "type": "about",
                "title": "About Us",
                "content": {
                    "text": "St. Vincent Pallotti School located in Podibahar, Ravi Shankar Shukla Nagar, Korba is a Co-educational Senior Secondary School affiliated to the Central Board of Secondary Education (CBSE), New Delhi on Provisional basis since 2007. It is one of the member institutes of Pallotti Group of Institutions. The school has been operating officially under the trust/society Korba Pallottine Shikshan Prothsahan Sangh.",
                    "additional": "The school is equipped with well furnished class rooms, library, laboratories, computer labs, music room, play ground and all essential facilities. If you are looking for details in admission/application forms, fees, school timings, vacation/holiday schedule or facility provided, kindly visit the relevant department of the school."
                }
            },
            "news": {
                "type": "news",
                "title": "Latest News",
                "content": {
                    "items": [
                        {
                            "date": "2021-07-03",
                            "title": "Environmental Day Celebration 2021",
                            "description": "Earth is our home and we must work hard to keep it protected and green. Wishing a very Happy World Environment Day to everyone. The occasion of World Environment Day reminds us of our responsibilities towards our planet. Let us wake up and make it a healthier and happier place.",
                            "has_video": True
                        }
                    ]
                }
            },
            "courses": {
                "type": "features",
                "title": "Courses",
                "content": {
                    "items": ["Maths", "Science", "Physics", "Art & Craft"]
                }
            },
            "principal_message": {
                "type": "custom",
                "title": "Principal's Message",
                "content": {
                    "text": "It is my pleasure and privilege to serve as the St. Vincent Pallotti School not only because teaching is my passion but also because I enjoy the company of my dear students also talented and zealous teachers.",
                    "additional": "We consider it a privilege to work with your kids every day to help them be their very best selves. We believe that each and every student has a gift to share with the world, and we work hard to unlock their highest potential. We have high expectations of our students, and we have high expectations of ourselves to help all St. Vincent Pallotti's students learn and grow into well-rounded citizens and critical thinkers."
                }
            },
            "events": {
                "type": "events",
                "title": "Events",
                "content": {
                    "items": [
                        "Cultural Activity",
                        "Co-Scholastic Activities",
                        "Olympiads & United Council Examination",
                        "Sports & Games",
                        "Celebration"
                    ]
                }
            }
        }
    },
    "about": {
        "title": "About",
        "slug": "about",
        "description": "Learn about St. Vincent Pallotti School's mission, vision, and values",
        "sections": {
            "goal": {
                "type": "custom",
                "title": "Goal",
                "content": {
                    "motto": "GO FORTH TO SERVE",
                    "text": "We form the children into responsible and caring persons, inculcating in them values of discipline punctuality, honesty, obedience and perseverance, so that they may progress in life, becoming integrated personalities. We ensure the development of persons sound in character, sharp in intellect and strong in body, ever willing to help and serve the society in times of need. Thus they fulfill the motto of our school.",
                    "additional": "We strive to equip our students with qualities of human values and strength of character to face any odds and oddities in life."
                }
            },
            "mission": {
                "type": "custom",
                "title": "Mission",
                "content": {
                    "text": "Our mission is to encourage and nurture the overall development of a child in view of academic cum co-curricular excellence with competence securing human values. We aim to provide each and every student an ideal learning environment to grow and excel from the time they begin their educational journey with us. Our highly effective and qualified teachers administer teaching modes that enable students to be knowledgeable learners."
                }
            },
            "aim_objectives": {
                "type": "custom",
                "title": "Aims & Objectives",
                "content": {
                    "intro": "St. Vincent Pallotti School aims to impart good education and discipline in order to make the students better citizens of tomorrow under the below mentioned objectives.",
                    "objectives": [
                        "To imbue in the children thirst for acquiring knowledge.",
                        "To instill in them moral virtues, indispensable in the making of good citizens and good human beings.",
                        "To develop in them a feeling of oneness, communal harmony, religious tolerance and patriotism.",
                        "To make children aware of their glorious past and cultural heritage.",
                        "To inculcate in them deep seated cultural values, which will bring out their essential Indian spirit.",
                        "To prepare them for global citizenship.",
                        "To make education a meaningful and enjoyable experience.",
                        "To cultivate the spirit of public speaking by organizing Assemblies, Elocution, Debates, Quiz and Dramatization.",
                        "To encourage our students in music, Casio, Harmonium, Tabla, Flute, individual solo songs, chorus group songs and Dance competition.",
                        "To organize Exhibition, by encouraging Art, Drawing, Painting, Arts, and Science workshop and Nature watching."
                    ]
                }
            },
            "principal_message": {
                "type": "custom",
                "title": "Principal's Message",
                "content": {
                    "paragraphs": [
                        "It is my pleasure and privilege to serve as the Principal of St. Vincent Pallotti School because teaching is my passion and also I wish to be a part in building our society with values and service for the humanity. In this school, I enjoy the company of my dear students and talented and zealous teachers.",
                        "We consider it a privilege to work with your kids every day to help them be their very best selves. We believe that each and every student has a gift to share with the world, and we work hard to unlock their highest potential. We have high expectations of our students, and we have high expectations of ourselves to help all St. Vincent Pallotti's students learn and grow into well-rounded citizens and critical thinkers.",
                        "We want each of our students to leave school with the values of respect, cooperation, persistence and striving for excellence underpinning all that they do. Our students develop responsibility for their own behaviour and the choices they make, and also a communal responsibility to assist their peers to do the same. Our students become strong in self-esteem and personal expectation and develop a healthy and respectful tolerance for others.",
                        "St. Vincent Pallotti School aims to develop leadership skills, social and emotional skills, and academic skills to prepare students for success not only in middle school but also in high school, career, relationships, and lifelong learning.",
                        "A child's school ought to be an extension of the family, providing a safe environment in which he/she can explore ideas and feelings."
                    ]
                }
            }
        },
        "children": ["goal", "mission", "aim", "principal-message", "mandatory-disclosure", "pallotti-group"]
    },
    "infrastructure": {
        "title": "Infrastructure",
        "slug": "infrastructure",
        "description": "Explore our state-of-the-art facilities and infrastructure",
        "sections": {
            "overview": {
                "type": "custom",
                "title": "Infrastructure Overview",
                "content": {
                    "paragraphs": [
                        "The Concept of the school building is unique. There are two different blocks, Viz one pre-primary cum primary block and another for the senior classes. The pre-primary block is specifically designed to help the children feel at home. Education is imparted here, not merely from books, but also through a planned scheme of activities. The well furnished classrooms are definitely spacious and airy. In addition to this, a play area cum garden with swings and see-saws and merry go rounds for the children, which give an atmosphere of a home away from home. In education friendly infrastructure is spread over 5 acres of land ample space for various Sports activity.",
                        "We have wonderful spacious New Building for our senior classes, that contains sufficient fans, lights, airy windows, comfort rooms, a lovely garden and open ground for sports and games."
                    ]
                }
            },
            "laboratory": {
                "type": "custom",
                "title": "Laboratory",
                "content": {
                    "text": "Students are encouraged to pursue Lab. We have huge well furnished and well equipped Labs for practicals. Ultra – modern and richly equipped laboratories for Physics, Biology, Chemistry etc. are the hallmarks of the school. A good number of maps, charts, models and instruments, decorate these labs."
                }
            },
            "library": {
                "type": "custom",
                "title": "Library",
                "content": {
                    "paragraphs": [
                        "We include a library period to 3rd and above classes. We have a good collection of Science, History, Geography, Computer and Literature books. We encourage our students to reading and reasoning through group discussions.",
                        "As soon as you enter the school library, the books will dazzle your eyes. The school has a rich and vast library. All sorts of books – Science, Arts, Commerce etc. – scatter radiant rays of knowledge and wisdom. Sundry journal, magazines and newspapers embellish the educational atmosphere and create an appetite for current affairs among the students. Keeping in view the advantage of the library, one library period is made compulsory for all classes. The students are free to borrow books and journals as per the library rules."
                    ]
                }
            },
            "computer_lab": {
                "type": "custom",
                "title": "Computer Lab",
                "content": {
                    "text": "The School has a two well furnished Labs to impart the knowledge to the children. One for the primary and one for the senior block. The computer lab is installed with the latest programs, in order to ensure that the Students get the most up-to-date knowledge of Information Technology. Students are taken to the Computer labs for practical. Each one is provided the opportunity to operate the computer. Each computer lab has sufficient number of computers for children to work with."
                }
            },
            "staff": {
                "type": "custom",
                "title": "Staff",
                "content": {
                    "text": "Teachers play a vital role in the formation of the personality of the children. They are backbone of any institution. The success of school is attributed to good administration, as well as to the dedication and devotion of the teachers. St. Vincent pallotti school aims at very efficient administration, aided by dedicated and well-trained staff, whose aim would be total commitment to all round excellence."
                }
            }
        },
        "children": ["laboratory", "library", "computer-lab", "staff"]
    },
    "admission": {
        "title": "Admission",
        "slug": "admission",
        "description": "Information about admissions, fees, and rules",
        "sections": {
            "admission_info": {
                "type": "custom",
                "title": "Admission Information",
                "content": {
                    "requirements": [
                        "The minimum age for admission to the Nursery class is 2½ – 3 Years and class PP-I is 3½ Years at the time of admission.",
                        "Parents/Guardians are requested to produce the Birth Certificate of the child issued by the Municipal Corporation/Gram Panchayat positively at the time of admission.",
                        "Parents will have a casual meeting with the principal. The principal's decision will be final concerning the admissions of the candidate.",
                        "A student coming from another school must submit the original Transfer Certificate from the school previously attended.",
                        "Student coming from other districts, states, or board shall submit the original Transfer Certificate duly countersigned by DEO/Authority of that District/Board.",
                        "If a child is admitted in the middle of a session, the maintenance fee of previous months has to be paid at the time of admission.",
                        "Provisional admission is given for a period of 15 days, and if the documents are not submitted within the stipulated time, the provisional certificate is automatically terminated.",
                        "Parents may please note that no child is automatically eligible for admission to this institution, unless the admission procedure is complete."
                    ]
                }
            },
            "rules_regulations": {
                "type": "custom",
                "title": "Rules and Regulations",
                "content": {
                    "rules": [
                        "The School Fee is to be paid in four installments i.e. April, July-September, October-December and January–March.",
                        "The Corporation Bank, 1st Floor, Sant Bhawan, Ghantaghar, Near Petrol Pump, Niharika, Korba collects the fee in the Bank, during the working hours.",
                        "Fees should be paid within the installment.",
                        "While paying fee, please make sure that the payment slips are dully in with Name, Surname, Class Section, Date and other particulars in BLOCK LETTERS.",
                        "No dues Form should be cleared before Mid-Term and Annual Examination. In case a student fails to clear the dues he/she may not be allowed to attend classes or examinations.",
                        "Fees should be paid on time. If the fee is not paid on time, Late Fine will be charged Rs. 100/- per month.",
                        "Cheque payment is accepted in the School Office.",
                        "If Cheque is bounced Rs. 100/- will be charged.",
                        "Fee paid is not refundable.",
                        "4th installment should be paid by 15th.",
                        "In addition to this kindly follow the fee schedule as shown in the payment slip."
                    ]
                }
            }
        }
    },
    "activity": {
        "title": "Activity",
        "slug": "activity",
        "description": "Cultural activities, sports, events and celebrations",
        "sections": {
            "cultural": {
                "type": "custom",
                "title": "Cultural Activity",
                "content": {
                    "text": "India is a land of vast and diverse cultures, castes, creeds and tradition. Even though every person follows the call of God in his/her own religion, it is important that every one of us learn to respect the other's. One of the way in which this institution tries to imbibe the cultural values by celebrating the main festivals of every religion."
                }
            },
            "co_scholastic": {
                "type": "custom",
                "title": "Co-Scholastic Activities",
                "content": {
                    "text": "Curricular and co-curricular activities help the students to grow in life activities and provide leadership training. The students organize various curricular and co-curricular activities such as Debate, Dramatics, Declamation, Singing, Drawing, Painting, Rangoli Competitions under the guidance of teachers."
                }
            },
            "olympiads": {
                "type": "custom",
                "title": "Olympiads & United Council Examination",
                "content": {
                    "text": "Our School is a centre for the Olympiads and united councils Tests/examination of All Indian Level. Our students participate willingly with the support of their parents."
                }
            },
            "sports": {
                "type": "custom",
                "title": "Sports & Games",
                "content": {
                    "text": "We encourage our students to participate in all indoor and outdoor games. We have Carrom Boards, Chess, Chinese Checkers and Table Tennis. We have separate rooms for Indoor games. We also have spacious ground for sports like Kabaddi, Kho-Kho. We have facility for many outdoor games like Football, Volleyball, Basketball and Cricket. All opportunities and guidance is provided to make our students healthy and sports person."
                }
            },
            "recent_activities": {
                "type": "news",
                "title": "Recent Activities",
                "content": {
                    "items": [
                        {"date": "2021-07-03", "title": "Environmental Day Celebration 2021", "description": "Earth is our home and we must work hard to keep it protected and green."},
                        {"date": "2021-04-30", "title": "School Reopens On 14/06/2021", "description": "School Reopens On 14/06/2021."},
                        {"date": "2021-03-27", "title": "New Session Commences On 01/04/2021", "description": "New Session Commences On 01/04/2021."},
                        {"date": "2021-03-15", "title": "Annual Result Will Be Declared On 27/03/2021", "description": "Annual Result Will Be Declared On 27/03/2021."},
                        {"date": "2020-12-15", "title": "Admissions Open For Nursery To Class XI from 15/01/2021", "description": "Admissions Open For Nursery To Class XI from 15/01/2021."}
                    ]
                }
            },
            "celebration": {
                "type": "custom",
                "title": "Celebration",
                "content": {
                    "text": "National festivals like Independence day, Republic day are celebrated with dignity, decorum and patriotic fervour. Teachers Day and Children's Day are also celebrated fairly and joyfully. Birthday of Teachers and Students come with anchoring melodious wishes \"Happy Birth Day to You\"."
                }
            }
        },
        "children": ["cultural-activity", "co-scholastic", "olympiads", "sports-games", "celebration"]
    },
    "downloads": {
        "title": "Downloads",
        "slug": "downloads",
        "description": "Download transfer certificates and forms",
        "sections": {
            "tc_download": {
                "type": "custom",
                "title": "TC Download",
                "content": {
                    "students": [
                        {"sn": 1, "name": "Ravindra Singh Thakur", "class": "IX"},
                        {"sn": 2, "name": "Nistha Patel", "class": "IX"},
                        {"sn": 3, "name": "Astha Patel", "class": "IX"},
                        {"sn": 4, "name": "Angel Mohanty", "class": "XI"},
                        {"sn": 5, "name": "Akshat Shrivastava", "class": "IX"}
                    ]
                }
            },
            "tc_form": {
                "type": "custom",
                "title": "TC Apply Form",
                "content": {
                    "fields": ["Name", "Roll Number", "Class", "Section", "Last Passed Out Year", "Email", "Message"]
                }
            }
        }
    },
    "academics": {
        "title": "Academics",
        "slug": "academics",
        "description": "Academic information, syllabus, and affiliation details",
        "sections": {
            "affiliation": {
                "type": "custom",
                "title": "Affiliation",
                "content": {
                    "documents": [
                        {"sn": "01", "name": "AFFILIATION LETTER"},
                        {"sn": "02", "name": "SOCIETY REGISTRATION CERTIFICATE"},
                        {"sn": "03", "name": "NO. OBJECTION CERTIFICATE"},
                        {"sn": "04", "name": "RECOGNITION CERTIFICATE RTE"},
                        {"sn": "05", "name": "BUILDING SAFETY CERTIFICATE"},
                        {"sn": "06", "name": "FIRE SAFETY CERTIFICATE"},
                        {"sn": "07", "name": "SELF CERTIFICATION BY SCHOOL"},
                        {"sn": "08", "name": "WATER, HEALTH AND SANITATION"},
                        {"sn": "09", "name": "FEE STRUCTURE OF THE SCHOOL"},
                        {"sn": "10", "name": "ANNUAL ACADEMIC CALENDAR"},
                        {"sn": "11", "name": "SCHOOL MANAGEMENT COMMITTEE (SMC)"},
                        {"sn": "12", "name": "PARENTS TEACHERS ASSOCIATION (PTA)"},
                        {"sn": "13", "name": "LAST THREE YEAR RESULT"},
                        {"sn": "14", "name": "STAFF & INFRASTRUCTURE DETAILS"}
                    ]
                }
            },
            "syllabus": {
                "type": "custom",
                "title": "Syllabus",
                "content": {
                    "paragraphs": [
                        "A special effort, made by the school to facilitate the total development of the child. Accordingly, a syllabus is designed, which combined intellectual data along with a great deal of personal activity. A qualified and expert panel staff members is appointed to periodically evaluate the syllabus and to suggest the necessary progress required in it.",
                        "We impart Education to our students through the upgraded syllabus of Central Board of secondary Education [C.B.S.E.] which adopts the Modern Methodology for comprehensive and integrated education of the students. Students are under continuous observation and are provided ample practical assignments. This inculcates in them more interests and pursuit of practical knowledge."
                    ]
                }
            },
            "subjects": {
                "type": "custom",
                "title": "Subjects Offered",
                "content": {
                    "classes": [
                        {"class": "Nursery", "subjects": "English, Hindi, Maths, EVS, Drawing"},
                        {"class": "PP-I & PP-II", "subjects": "English, Hindi, Maths, EVS, Drawing, Art & Craft"},
                        {"class": "CLASS I & V", "subjects": "English, Hindi, Maths, EVS, Computer, G.K., Moral Science, Art & Craft"},
                        {"class": "CLASS VI & VIII", "subjects": "English, Hindi, Sanskrit, Maths, Science, Social Science, Computer, G.K., Moral Science, Drawing, Art & Craft"},
                        {"class": "CLASS IX & X", "subjects": "English, Hindi, Maths, Science, Social Science, Information Technology, Moral Science"},
                        {"class": "CLASS XI & XII", "subjects": "English, Maths, Bio., Physics, Chem., Computer Science, Physical Edu., Commerce Stream"}
                    ]
                }
            },
            "ptm": {
                "type": "custom",
                "title": "PTM",
                "content": {
                    "description": "There will be PTM after every examination. The purpose of the PTM is to provide the parents an opportunity to catch up with the performance and the progress of their wards also if any child is found to be performing in a manner that is not satisfactory. Parents will be advised to pay more attention to the efforts put in by their wards. Constructive suggestion will be appreciated. Parents are allowed to meet the respective teachers on Saturdays between 12:00 am to 12:30 pm. Parents are not allowed to interact with any teacher during the teaching hours in class. This will help them to guide and help their wards in a better way.",
                    "schedule": [
                        {"ptm": "PTM – II will be held on", "date": "24/10/2019", "time": "11:30 AM"},
                        {"ptm": "PTM After Quarterly Exam", "date": "12/01/2019", "time": "11:30 AM"}
                    ]
                }
            },
            "scholarship": {
                "type": "custom",
                "title": "Scholarship",
                "content": {
                    "categories": [
                        {"class": "Pre-Primary [Nursery to PP-II]", "prize": "Rs. 1000/-", "count": 3},
                        {"class": "Primary Classes [I-V]", "prize": "Rs. 1000/-", "count": 3},
                        {"class": "Middle Classes [VI-VIII]", "prize": "Rs. 1500/-", "count": 3},
                        {"class": "Secondary Classes [IX-X]", "prize": "Rs. 1500/-", "count": 3},
                        {"class": "Senior Secondary Classes [XI-XII]", "prize": "Rs. 2000/-", "count": 3}
                    ],
                    "note": "Each winner will be awarded with a cash prize and a Certificate of Appreciation/Excellence."
                }
            }
        },
        "children": ["affiliation", "syllabus", "subjects-offered", "ptm", "scholarship", "book-list"]
    },
    "contact": {
        "title": "Contact Us",
        "slug": "contact",
        "description": "Get in touch with St. Vincent Pallotti School",
        "sections": {
            "location": {
                "type": "contact",
                "title": "Our Location",
                "content": {
                    "address": "RAVISHANKAR SHUKLA NAGAR, PODIBAHAR, KORBA C.G.",
                    "phones": {
                        "primary_block": "07566665445",
                        "secondary_block": "09522945397",
                        "school_office": "08463097907"
                    },
                    "emails": [
                        "svpspodibahar@yahoo.co.in",
                        "svpspodibahar@gmail.com"
                    ]
                }
            }
        }
    }
}

# Navigation menu structure
NAVIGATION_MENUS = [
    {
        "title": "Home",
        "slug": "home",
        "href": "/",
        "menu_type": "page",
        "display_order": 1,
        "show_in_navigation": True,
        "show_in_landing_page": True,
        "children": []
    },
    {
        "title": "About",
        "slug": "about",
        "href": "/about",
        "menu_type": "dropdown",
        "display_order": 2,
        "show_in_navigation": True,
        "children": [
            {"title": "About Us", "slug": "about-us", "href": "/about/about-us", "display_order": 1},
            {"title": "Goal", "slug": "goal", "href": "/about/goal", "display_order": 2},
            {"title": "Mission", "slug": "mission", "href": "/about/mission", "display_order": 3},
            {"title": "Aims & Objectives", "slug": "aim", "href": "/about/aim", "display_order": 4},
            {"title": "Principal's Message", "slug": "principal-message", "href": "/about/principal-message", "display_order": 5},
            {"title": "Mandatory Disclosure", "slug": "mandatory-disclosure", "href": "/about/mandatory-disclosure", "display_order": 6},
            {"title": "Pallotti Group", "slug": "pallotti-group", "href": "/about/pallotti-group", "display_order": 7},
        ]
    },
    {
        "title": "Infrastructure",
        "slug": "infrastructure",
        "href": "/infrastructure",
        "menu_type": "dropdown",
        "display_order": 3,
        "show_in_navigation": True,
        "children": [
            {"title": "Infrastructure", "slug": "infrastructure-overview", "href": "/infrastructure/overview", "display_order": 1},
            {"title": "Gallery", "slug": "infrastructure-gallery", "href": "/infrastructure/gallery", "display_order": 2},
            {"title": "Laboratory", "slug": "laboratory", "href": "/infrastructure/laboratory", "display_order": 3},
            {"title": "Library", "slug": "library", "href": "/infrastructure/library", "display_order": 4},
            {"title": "Computer Lab", "slug": "computer-lab", "href": "/infrastructure/computer-lab", "display_order": 5},
            {"title": "Staff", "slug": "staff", "href": "/infrastructure/staff", "display_order": 6},
        ]
    },
    {
        "title": "Admission",
        "slug": "admission",
        "href": "/admission",
        "menu_type": "dropdown",
        "display_order": 4,
        "show_in_navigation": True,
        "children": [
            {"title": "Admission", "slug": "admission-info", "href": "/admission/info", "display_order": 1},
            {"title": "Admission Fee", "slug": "admission-fee", "href": "/admission/fee", "display_order": 2},
            {"title": "Rules & Regulations", "slug": "rules-regulations", "href": "/admission/rules", "display_order": 3},
        ]
    },
    {
        "title": "Activity",
        "slug": "activity",
        "href": "/activity",
        "menu_type": "dropdown",
        "display_order": 5,
        "show_in_navigation": True,
        "children": [
            {"title": "Cultural Activity", "slug": "cultural-activity", "href": "/activity/cultural", "display_order": 1},
            {"title": "Co-Scholastic Activities", "slug": "co-scholastic", "href": "/activity/co-scholastic", "display_order": 2},
            {"title": "Olympiads & UCE", "slug": "olympiads", "href": "/activity/olympiads", "display_order": 3},
            {"title": "Sports & Games", "slug": "sports-games", "href": "/activity/sports", "display_order": 4},
            {"title": "Recent Activity", "slug": "recent-activity", "href": "/activity/recent", "display_order": 5},
            {"title": "Celebration", "slug": "celebration", "href": "/activity/celebration", "display_order": 6},
        ]
    },
    {
        "title": "Downloads",
        "slug": "downloads",
        "href": "/downloads",
        "menu_type": "dropdown",
        "display_order": 6,
        "show_in_navigation": True,
        "children": [
            {"title": "TC Download", "slug": "tc-download", "href": "/downloads/tc", "display_order": 1},
            {"title": "TC Apply Form", "slug": "tc-apply", "href": "/downloads/tc-apply", "display_order": 2},
        ]
    },
    {
        "title": "Academics",
        "slug": "academics",
        "href": "/academics",
        "menu_type": "dropdown",
        "display_order": 7,
        "show_in_navigation": True,
        "children": [
            {"title": "Affiliation", "slug": "affiliation", "href": "/academics/affiliation", "display_order": 1},
            {"title": "Syllabus", "slug": "syllabus", "href": "/academics/syllabus", "display_order": 2},
            {"title": "Subjects Offered", "slug": "subjects-offered", "href": "/academics/subjects", "display_order": 3},
            {"title": "PTM", "slug": "ptm", "href": "/academics/ptm", "display_order": 4},
            {"title": "Scholarship", "slug": "scholarship", "href": "/academics/scholarship", "display_order": 5},
            {"title": "Book List 2023-24", "slug": "book-list", "href": "/academics/book-list", "display_order": 6},
        ]
    },
    {
        "title": "Affiliation",
        "slug": "affiliation-main",
        "href": "/affiliation",
        "menu_type": "page",
        "display_order": 8,
        "show_in_navigation": True,
        "children": []
    },
    {
        "title": "Contact Us",
        "slug": "contact",
        "href": "/contact",
        "menu_type": "page",
        "display_order": 9,
        "show_in_navigation": True,
        "show_in_footer": True,
        "children": []
    },
]


class Command(BaseCommand):
    help = 'Seed the database with St. Vincent Pallotti School content from stvincent.md'

    def add_arguments(self, parser):
        parser.add_argument(
            '--school-slug',
            type=str,
            default='stvincentpallottikorba',
            help='Slug of the school to seed content for (default: stvincentpallottikorba)'
        )
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Overwrite existing content'
        )
        parser.add_argument(
            '--menus-only',
            action='store_true',
            help='Only create/update navigation menus'
        )
        parser.add_argument(
            '--pages-only',
            action='store_true',
            help='Only create/update pages and sections'
        )

    def handle(self, *args, **options):
        school_slug = options['school_slug']
        overwrite = options['overwrite']
        menus_only = options['menus_only']
        pages_only = options['pages_only']

        # Get or create the school
        try:
            school = School.objects.get(slug=school_slug)
            organization = school.organization
            self.stdout.write(self.style.SUCCESS(
                f'Found existing school: {school.name}'
            ))
        except School.DoesNotExist:
            # Create organization and school
            organization = Organization.objects.create(
                name='St. Vincent Pallotti School Korba',
                slug='stvincent-korba',
                email='svpspodibahar@gmail.com',
                phone='08463097907',
                address='Ravi Shankar Shukla Nagar, Podibahar',
                city='Korba',
                state='Chhattisgarh',
                country='India',
                postal_code='495677',
                is_active=True,
                is_verified=True
            )
            school = School.objects.create(
                organization=organization,
                name='St. Vincent Pallotti School',
                slug=school_slug,
                short_name='SVPS Korba',
                tagline='Go Forth To Serve',
                description='St. Vincent Pallotti School located in Podibahar, Korba is a Co-educational Senior Secondary School affiliated to CBSE.',
                established_year=2007,
                email='svpspodibahar@gmail.com',
                phone='08463097907',
                website='https://pallottischoolkorba.edu.in',
                address_line1='Ravi Shankar Shukla Nagar',
                address_line2='Podibahar',
                city='Korba',
                state='Chhattisgarh',
                country='India',
                postal_code='495677',
                is_active=True,
                config={
                    'affiliation_no': '3330106',
                    'school_code': '15244',
                    'board': 'CBSE'
                }
            )
            self.stdout.write(self.style.SUCCESS(
                f'Created new school: {school.name}'
            ))

        # Create menus
        if not pages_only:
            self.create_navigation_menus(organization, school, overwrite)

        # Create pages and sections
        if not menus_only:
            self.create_pages_and_sections(organization, school, overwrite)

        self.stdout.write(self.style.SUCCESS('\n✅ Seeding complete!'))

    def create_navigation_menus(self, organization, school, overwrite):
        """Create navigation menu structure"""
        self.stdout.write(self.style.NOTICE('\n📁 Creating navigation menus...'))

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for menu_data in NAVIGATION_MENUS:
            children = menu_data.pop('children', [])

            # Check if menu exists
            existing = NavigationMenu.objects.filter(
                organization=organization,
                school=school,
                slug=menu_data['slug'],
                parent__isnull=True
            ).first()

            if existing and not overwrite:
                self.stdout.write(f'  Skipping menu: {menu_data["title"]}')
                skipped_count += 1
                parent_menu = existing
            elif existing:
                # Update existing
                for key, value in menu_data.items():
                    setattr(existing, key, value)
                existing.save()
                self.stdout.write(self.style.SUCCESS(f'  Updated menu: {menu_data["title"]}'))
                updated_count += 1
                parent_menu = existing
            else:
                # Create new
                parent_menu = NavigationMenu.objects.create(
                    organization=organization,
                    school=school,
                    parent=None,
                    is_active=True,
                    show_in_footer=menu_data.get('show_in_footer', False),
                    show_in_landing_page=menu_data.get('show_in_landing_page', False),
                    **{k: v for k, v in menu_data.items() if k not in ['show_in_footer', 'show_in_landing_page']}
                )
                self.stdout.write(self.style.SUCCESS(f'  Created menu: {menu_data["title"]}'))
                created_count += 1

            # Create children
            for child_data in children:
                child_existing = NavigationMenu.objects.filter(
                    organization=organization,
                    school=school,
                    slug=child_data['slug'],
                    parent=parent_menu
                ).first()

                if child_existing and not overwrite:
                    skipped_count += 1
                elif child_existing:
                    for key, value in child_data.items():
                        setattr(child_existing, key, value)
                    child_existing.save()
                    updated_count += 1
                else:
                    NavigationMenu.objects.create(
                        organization=organization,
                        school=school,
                        parent=parent_menu,
                        menu_type='page',
                        is_active=True,
                        show_in_navigation=True,
                        **child_data
                    )
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nMenus: Created={created_count}, Updated={updated_count}, Skipped={skipped_count}'
        ))

    def create_pages_and_sections(self, organization, school, overwrite):
        """Create pages and their sections"""
        self.stdout.write(self.style.NOTICE('\n📄 Creating pages and sections...'))

        page_created = 0
        page_updated = 0
        page_skipped = 0
        section_created = 0
        section_updated = 0

        for page_key, page_data in SCHOOL_CONTENT.items():
            sections_data = page_data.pop('sections', {})
            page_data.pop('children', None)  # Remove children key if present

            # Check if page exists
            existing_page = Page.objects.filter(
                organization=organization,
                school=school,
                slug=page_data['slug']
            ).first()

            if existing_page and not overwrite:
                self.stdout.write(f'  Skipping page: {page_data["title"]}')
                page_skipped += 1
                page = existing_page
            elif existing_page:
                existing_page.title = page_data['title']
                existing_page.description = page_data['description']
                existing_page.meta_title = page_data['title']
                existing_page.meta_description = page_data['description'][:160]
                existing_page.is_published = True
                existing_page.published_at = timezone.now()
                existing_page.save()
                self.stdout.write(self.style.SUCCESS(f'  Updated page: {page_data["title"]}'))
                page_updated += 1
                page = existing_page
            else:
                page = Page.objects.create(
                    organization=organization,
                    school=school,
                    title=page_data['title'],
                    slug=page_data['slug'],
                    description=page_data['description'],
                    meta_title=page_data['title'],
                    meta_description=page_data['description'][:160],
                    is_published=True,
                    published_at=timezone.now()
                )
                self.stdout.write(self.style.SUCCESS(f'  Created page: {page_data["title"]}'))
                page_created += 1

            # Create sections for the page
            order = 0
            for section_key, section_data in sections_data.items():
                order += 1
                section_slug = slugify(section_key)

                existing_section = Section.objects.filter(
                    organization=organization,
                    school=school,
                    page=page,
                    slug=section_slug
                ).first()

                if existing_section and not overwrite:
                    continue
                elif existing_section:
                    existing_section.title = section_data['title']
                    existing_section.section_type = section_data['type']
                    existing_section.content = section_data['content']
                    existing_section.display_order = order
                    existing_section.is_visible = True
                    existing_section.save()
                    section_updated += 1
                else:
                    Section.objects.create(
                        organization=organization,
                        school=school,
                        page=page,
                        title=section_data['title'],
                        slug=section_slug,
                        section_type=section_data['type'],
                        content=section_data['content'],
                        display_order=order,
                        is_visible=True
                    )
                    section_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nPages: Created={page_created}, Updated={page_updated}, Skipped={page_skipped}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'Sections: Created={section_created}, Updated={section_updated}'
        ))
