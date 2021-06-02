from core.serializers.UserSerializer import UserSerializer
from core.serializers.LedgerSerializer import LedgerSerializer
from rest_framework import viewsets
from django.contrib.auth.models import User
from rest_framework.decorators import action
from core.models import GroupMapping, Ledger
from rest_framework .response import Response
from rest_framework import status
from core.models import Group
from django.utils.datastructures import MultiValueDictKeyError
import pdb
from django.db.models import Sum


def intervals(parts, duration):
    part_duration = duration / parts
    return [abs((i * part_duration - (i + 1) * part_duration)) for i in range(parts)]


SPLIT_UNEQUAL = "split_unequal"
SPLIT_EQUAL = "split_equal"

SPLIT_BY_PERCENTAGE = "split_by_percentage"
SPLIT_BY_AMOUNT = "split_by_amount"

SPLIT_STRATEGIES = [
    SPLIT_EQUAL,
    SPLIT_UNEQUAL
]

SPLIT_UNEQUAL_STRATEGIES = [
    SPLIT_BY_PERCENTAGE,
    SPLIT_BY_AMOUNT
]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def make_settlement_transaction(self,
                                    from_user,
                                    to_user,
                                    group,
                                    amount):
        # maker
        Ledger.objects.create(
            from_user=from_user,
            to_user=to_user,
            group=group,
            amount=amount
        )

        # checker
        Ledger.objects.create(
            from_user=to_user,
            to_user=from_user,
            group=group,
            amount=-amount
        )

    def split_amount(self, users, amount,  split_strategy, split_unequal_strategy, request_params):
        if(split_strategy == SPLIT_EQUAL):
            parts = len(users)

            amount_list = intervals(parts, amount)

            return zip(users, amount_list)
        elif(split_strategy == SPLIT_UNEQUAL):
            number_of_users = len(users)
            if(split_unequal_strategy == SPLIT_BY_PERCENTAGE):
                percentage_list = request_params.getlist('percentage[]')
                percentage_list = [int(x) for x in percentage_list]
                if (len(percentage_list) != number_of_users
                        or
                        sum(percentage_list) != 100):
                    raise Exception(
                        "Please send same number of percentages as users and make sure it adds upto 100")
                amount_list = []
                for percentage in percentage_list:
                    amount_list.append(amount * percentage/100)
                return zip(users, amount_list)
            elif(split_unequal_strategy == SPLIT_BY_AMOUNT):
                pass

        return zip(users, amount_list)

    @action(detail=True, methods=['get'])
    def get_ledger_for_group(self, request, pk=None):
        request_params = request.query_params
        user = self.get_object()

        try:
            group_id = request_params['group_id'][0]
        except MultiValueDictKeyError:
            group_id = 1
            # return Response(
            #     {
            #         'status': status.HTTP_400_BAD_REQUEST,
            #         'message': "Please send 'group_id' as query parameter"
            #     }
            # )

        try:
            group = Group.objects.get(id=group_id)
        except (Group.DoesNotExist, MultiValueDictKeyError):
            return Response(
                {
                    'status': status.HTTP_400_BAD_REQUEST,
                    'message': "Group Does Not Exist"
                }
            )

        ledger_aggregate = Ledger.objects.filter(
            from_user=user, group=group
        ).values('to_user', 'from_user').order_by('to_user').annotate(
            final_amount=Sum('amount')
        )

        return Response(
            {'status': status.HTTP_200_OK, 'balance_sheet': ledger_aggregate}
        )

    @action(detail=True, methods=['post'])
    def create_expense(self, request, pk=None):

        try:
            request_params = request.data
            user = self.get_object()
            to_user = User.objects.get(id=request_params['to_user_id'])
            group = Group.objects.get(id=request_params['group_id'])
            amount = int(request_params['amount'])

            message = ""

            self.make_settlement_transaction(
                from_user=user,
                to_user=to_user,
                group=group,
                amount=-amount
            )

            message += f'{user.username} lost {amount}\n'
            message += f'{to_user.username} gained {amount}'

            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': message
                }
            )

        except Exception as e:
            return Response(
                {'status': status.HTTP_400_BAD_REQUEST, 'message': str(e)}
            )

    @action(detail=True, methods=['post'])
    def create_group_expense(self, request, pk=None):
        try:
            request_params = request.data
            user = self.get_object()

            group = Group.objects.get(id=request_params['group_id'])

            split_strategy = request_params['split_strategy'] or SPLIT_EQUAL
            split_unequal_strategy = None
            if split_strategy == SPLIT_UNEQUAL:
                split_unequal_strategy = request_params['split_unequal_strategy'] or SPLIT_BY_AMOUNT

            amount = int(request_params['amount'])

            if split_strategy not in SPLIT_STRATEGIES:
                raise Exception("Invalid Split Strategy")
            if split_strategy == SPLIT_UNEQUAL and split_unequal_strategy not in SPLIT_UNEQUAL_STRATEGIES:
                raise Exception("Invalid Split Unequal Strategy")

            mapping_list = GroupMapping.objects.filter(
                group=group)
            users = [mapping.user for mapping in mapping_list]

            user_amount_zip = self.split_amount(
                users,
                amount,
                split_strategy,
                split_unequal_strategy,
                request_params
            )

            message = ""

            for to_user, part_amount in user_amount_zip:
                message += f'{user.username} lost {part_amount}'
                message += f'{to_user.username} gained {part_amount}'
                self.make_settlement_transaction(
                    from_user=user,
                    to_user=to_user,
                    group=group,
                    amount=-part_amount
                )
            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': message
                }
            )

        except Exception as e:
            raise e
            return Response(
                {'status': status.HTTP_400_BAD_REQUEST, 'message': str(e)}
            )

    @action(detail=True, methods=['post'])
    def make_payment_to_user(self, request, pk=None):
        try:
            request_params = request.data

            user = self.get_object()
            to_user = User.objects.get(id=request_params['to_user_id'])
            group = Group.objects.get(id=request_params['group_id'])
            amount = int(request_params['amount'])

            message = ""

            self.make_settlement_transaction(from_user=user,
                                             to_user=to_user,
                                             group=group,
                                             amount=-amount)

            message += f'{to_user.username} gained {amount}\n'
            message += f'{user.username} lost {amount}'

            return Response(
                {
                    'status': status.HTTP_200_OK,
                    'message': message
                }
            )
        except Exception as e:
            return Response(
                {'status': status.HTTP_400_BAD_REQUEST, 'message': str(e)}
            )
